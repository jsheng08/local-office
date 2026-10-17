import type { Card, Priority } from '../../../types/office'
export const priorities: { id: Priority; label: string; color: string }[] = [
  { id: 'must', label: 'Must-have', color: '#e5484d' },
  { id: 'should', label: 'Should-have', color: '#f5a524' },
  { id: 'could', label: 'Nice-to-have', color: '#3fb26f' },
  { id: 'wont', label: 'Later', color: '#8a949b' },
]
export const priorityLabel = (id: Priority) => priorities.find(p => p.id === id)?.label ?? id
export const hours = (value?: number) => value != null && Number.isFinite(value) ? new Intl.NumberFormat(undefined, { maximumFractionDigits: 1 }).format(value) : '—'
export const changeLabel = (card: Card) => card.change === 'added' ? 'NEW' : card.change === 'removed' ? 'DEFERRED / REMOVED' : card.change === 'modified' ? (card.beforePriority && card.beforePriority !== card.priority ? `↑ ${priorityLabel(card.beforePriority)} → ${priorityLabel(card.priority)}` : 'MODIFIED') : ''
export const initials = (name: string) => name.trim().split(/\s+/).filter(Boolean).map(word => Array.from(word)[0]).slice(0, 2).join('')
export const avatarColor = (id: string) => {
  let hash = 0
  for (const char of id) hash = (Math.imul(hash, 31) + char.charCodeAt(0)) | 0
  return `hsl(${Math.abs(hash) % 360} 42% 35%)`
}
