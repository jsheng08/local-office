CONFIDENTIAL – SYNTHETIC DEMO DATA
# SPL Driver & Dispatch Portal — Client Brief v2 (2026-10-14)
Client: Sinar Pantai Logistics Sdn Bhd (SPL). Prepared for: Teratai Digital Sdn Bhd.

Revision notes (v2, 2026-10-14):
- §6 deferred to Phase 2.
- §8 changed: IC handling now a must-have with PDPA controls.
- §9 changed: go-live pulled forward to 2027-01-15.
- §11 added: LHDN MyInvois e-invoicing.

§1. Background: Sinar Pantai Logistics operates 40 depots and around 600 delivery drivers across Peninsular Malaysia. Dispatch is currently coordinated by phone and spreadsheets, which causes missed deliveries and poor visibility for management. SPL wants a single portal connecting drivers, dispatchers and customers.

§2. Driver mobile app: Drivers must have a mobile app showing their assigned deliveries for the day. The app must capture proof of delivery, including a photo of the parcel and the recipient's signature. This is a must-have for launch.

§3. Dispatcher dashboard: Dispatchers need a web dashboard with a live map showing driver locations and delivery status. Updates should be "real-time" so dispatchers can reassign jobs quickly. Dispatchers should be able to filter by depot and route.

§4. Customer notifications: Customers should receive SMS or WhatsApp notifications when their delivery is dispatched, nearby, and completed. Messages must be available in Bahasa Malaysia and English. Customers should be able to choose their preferred language.

§5. ERP integration: The portal must integrate with SPL's legacy ERP system for orders and invoicing. The integration should be done via the usual method used by our IT team. Order data must flow into the portal without manual re-entry.

§6. [REMOVED – deferred to Phase 2] Monthly KPI reports for management.

§7. Offline mode: Drivers on rural East Coast routes often lose mobile coverage. The driver app must continue to work offline and sync proof of delivery once connectivity returns. No delivery record may be lost during sync.

§8. COD verification: For cash-on-delivery orders, the system must store customer IC numbers to verify the recipient's identity. IC numbers must be masked in all screens, encrypted at rest, retained for no more than 90 days, and PDPA consent must be captured in-app before collection. This is now a must-have and must be completed before UAT on 2026-12-15.

§9. Timeline: The go-live date is pulled forward to 2027-01-15, ahead of the Chinese New Year peak. SPL expects a pilot at two depots before full rollout.

§10. Budget: The total budget ceiling for this phase is RM 480,000. Any change requests beyond this ceiling require SPL management approval.

§11. E-invoicing: The portal must integrate with LHDN MyInvois e-invoicing to issue e-invoices for COD receipts. This is mandatory by 2027-01-01 to meet regulatory requirements.
