FROM node:20-slim AS base

WORKDIR /app


FROM base AS dependencies

COPY package*.json ./
RUN npm ci


FROM dependencies AS development

CMD ["npm", "run", "dev"]


FROM dependencies AS builder

COPY . .
RUN npm run build


FROM base AS production

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

CMD ["node", "server.js"]
