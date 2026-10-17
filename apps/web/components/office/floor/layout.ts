import type { Card, Priority, Staff } from '~/types/office'

export interface BedPlacement { card: Card; color: string; x: number; y: number }
const lanes: { key: Priority; label: string; color: string }[] = [
  { key: 'must', label: 'ER · MUST', color: '#e5484d' },
  { key: 'should', label: 'WARD · SHOULD', color: '#f5a524' },
  { key: 'could', label: 'CLINIC · NICE', color: '#3fb26f' },
  { key: 'wont', label: 'WAITING ROOM · LATER', color: '#8a949b' },
]
export function wardLayout(cards: Card[]) {
  return lanes.map((lane, index) => {
    const patients = cards.filter(card => (card.change === 'removed' ? 'wont' : card.priority) === lane.key)
    const x = 86 + index * 277
    return { ...lane, x, total: patients.length, beds: patients.slice(0, 6).map((card, slot) => ({
      card, color: lane.color, x: x + 17 + slot % 2 * 130, y: -244 + Math.floor(slot / 2) * 94,
    })) }
  })
}
export function staffPlacements(staff: Staff[], cards: Card[], beds: BedPlacement[], desks: { person: Staff; x: number; y: number }[], iso: (x: number, y: number) => readonly [number, number]) {
  return staff.filter(person => !person.on_leave).flatMap(person => {
    const patients = cards.filter(card => card.change !== 'removed' && card.staff.some(member => member.staff_id === person.id))
    const bed = beds.find(bed => patients.some(card => card.id === bed.card.id))
    const desk = desks.find(desk => desk.person.id === person.id)
    if (!bed && !desk) return []
    const colleagues = bed?.card.staff.filter(member => staff.some(candidate => candidate.id === member.staff_id && !candidate.on_leave)) || []
    const slot = colleagues.findIndex(member => member.staff_id === person.id)
    const [x, y] = bed ? [bed.x + 88 + (slot % 2) * 18, bed.y + 23 + Math.floor(slot / 2) * 28] : iso(desk!.x + .8, desk!.y + 1)
    return [{ person, x, y, patients: patients.length, proposed: patients.some(card => card.proposed) }]
  })
}
