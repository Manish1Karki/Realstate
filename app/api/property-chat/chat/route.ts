import { createPropertyChatHandler } from '../../../../lib/property-chat/server.mjs'

export const runtime = 'nodejs'
export const maxDuration = 120

export const POST = createPropertyChatHandler()
