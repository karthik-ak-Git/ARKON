import { ResourceRequirements, ResourceAvailability } from './types.js'

interface Allocation {
  jobId: string
  resources: ResourceRequirements
  allocatedAt: number
}

export class ResourceMonitorImpl {
  private _total: ResourceAvailability
  private _allocated: Map<string, ResourceRequirements> = new Map()
  private _allocations: Allocation[] = []

  constructor(total: ResourceAvailability) {
    this._total = { ...total }
  }

  getAvailability(): ResourceAvailability {
    const used = this.getUsed()
    return {
      cpu: Math.max(0, this._total.cpu - used.cpu),
      memoryMb: Math.max(0, this._total.memoryMb - used.memoryMb),
      diskMb: Math.max(0, this._total.diskMb - used.diskMb),
      gpu: this._total.gpu !== undefined
        ? Math.max(0, (this._total.gpu ?? 0) - (used.gpu ?? 0))
        : undefined,
      custom: this._total.custom
        ? Object.fromEntries(
            Object.entries(this._total.custom).map(([key, total]) => [
              key,
              Math.max(0, total - (used.custom?.[key] ?? 0)),
            ])
          )
        : undefined,
    }
  }

  getUsed(): ResourceRequirements {
    const used: ResourceRequirements = {
      cpu: 0,
      memoryMb: 0,
      diskMb: 0,
      gpu: 0,
      custom: {},
    }

    for (const alloc of this._allocated.values()) {
      used.cpu += alloc.cpu
      used.memoryMb += alloc.memoryMb
      used.diskMb += alloc.diskMb
      if (alloc.gpu) used.gpu = (used.gpu ?? 0) + alloc.gpu
      if (alloc.custom) {
        for (const [key, value] of Object.entries(alloc.custom)) {
          used.custom![key] = (used.custom![key] ?? 0) + value
        }
      }
    }

    return used
  }

  canAllocate(resources: ResourceRequirements): boolean {
    const available = this.getAvailability()
    if (available.cpu < resources.cpu) return false
    if (available.memoryMb < resources.memoryMb) return false
    if (available.diskMb < resources.diskMb) return false
    if (resources.gpu && (!available.gpu || available.gpu < resources.gpu)) return false
    if (resources.custom) {
      for (const [key, value] of Object.entries(resources.custom)) {
        if ((available.custom?.[key] ?? 0) < value) return false
      }
    }
    return true
  }

  allocate(jobId: string, resources: ResourceRequirements): boolean {
    if (!this.canAllocate(resources)) {
      return false
    }
    this._allocated.set(jobId, resources)
    this._allocations.push({
      jobId,
      resources,
      allocatedAt: Date.now(),
    })
    return true
  }

  release(jobId: string): void {
    this._allocated.delete(jobId)
    this._allocations = this._allocations.filter(a => a.jobId !== jobId)
  }

  getUtilization(): ResourceAvailability {
    const availability = this.getAvailability()
    return {
      cpu: this._total.cpu > 0 ? ((this._total.cpu - availability.cpu) / this._total.cpu) * 100 : 0,
      memoryMb: this._total.memoryMb > 0 ? ((this._total.memoryMb - availability.memoryMb) / this._total.memoryMb) * 100 : 0,
      diskMb: this._total.diskMb > 0 ? ((this._total.diskMb - availability.diskMb) / this._total.diskMb) * 100 : 0,
      gpu: this._total.gpu !== undefined && this._total.gpu > 0
        ? (((this._total.gpu ?? 0) - (availability.gpu ?? 0)) / (this._total.gpu ?? 1)) * 100
        : undefined,
    }
  }

  getAllocations(): ReadonlyArray<Allocation> {
    return [...this._allocations]
  }

  getAllocation(jobId: string): ResourceRequirements | undefined {
    const alloc = this._allocated.get(jobId)
    return alloc ? { ...alloc } : undefined
  }

  getTotal(): Readonly<ResourceAvailability> {
    return { ...this._total }
  }
}