import type { Card, Staff } from '~/types/office'

export const numeric = (value: any): number | null =>
  value == null || isNaN(Number(value)) ? null : Number(value)

// Keep the arithmetic identical to brief.vue; missing sides exclude the whole change.
export function changeCost(changes: any[]) {
  let hours = 0, added = 0, modified = 0, removed = 0, missing = 0
  for (const c of changes) {
    if (c.change === 'added') { added++; const a = numeric(c.after?.pert); a == null ? missing++ : (hours += a) }
    else if (c.change === 'modified') { modified++; const a = numeric(c.after?.pert), b = numeric(c.before?.pert); a == null || b == null ? missing++ : (hours += a - b) }
    else if (c.change === 'removed') { removed++; const b = numeric(c.before?.pert); b == null ? missing++ : (hours -= b) }
  }
  return { hours, added, modified, removed, missing }
}

export function sumEstimates(estimates: any[], field: string) {
  let total = 0, missing = 0
  for (const estimate of estimates) {
    const value = numeric(estimate?.[field])
    if (value == null) missing++
    else total += value
  }
  return { total, missing }
}

export function staffing(cards: Card[], staff: Staff[]) {
  return staff.flatMap(person => {
    const recommended = cards.filter(card => card.staff.some(s => s.staff_id === person.id))
    return recommended.length ? [{ person, cards: recommended, estimate: sumEstimates(recommended.map(c => c.est), 'pert') }] : []
  })
}
