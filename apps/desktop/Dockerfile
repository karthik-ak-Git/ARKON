FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml ./
RUN corepack enable && corepack prepare pnpm@9.7.1 --activate

COPY apps/desktop/package.json apps/desktop/pnpm-workspace.yaml ./
COPY packages/shared/package.json packages/agent-sdk/package.json ./packages/

RUN pnpm install --frozen-lockfile

COPY apps/desktop/ ./apps/desktop/
COPY packages/shared/ ./packages/shared/
COPY packages/agent-sdk/ ./packages/agent-sdk/

WORKDIR /app/apps/desktop
RUN pnpm build

FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app/apps/desktop/dist ./dist
COPY --from=builder /app/apps/desktop/index.html ./index.html
COPY --from=builder /app/apps/desktop/public ./public

EXPOSE 8080

CMD ["npx", "serve", "-s", ".", "-l", "8080"]