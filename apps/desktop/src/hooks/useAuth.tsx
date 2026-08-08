import React, { createContext, useContext, useState, useEffect } from 'react'

interface User {
  id: string
  email: string
  name: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('arkon_token')
    if (token) {
      setUser({ id: '1', email: 'admin@arkon.dev', name: 'Admin' })
    }
    setIsLoading(false)
  }, [])

  const login = async (email: string, _password: string) => {
    const mockUser: User = { id: '1', email, name: 'Admin' }
    setUser(mockUser)
    localStorage.setItem('arkon_token', 'mock-token')
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('arkon_token')
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
