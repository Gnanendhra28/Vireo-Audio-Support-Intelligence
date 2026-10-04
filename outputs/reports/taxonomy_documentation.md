# SEVEN-PILLAR SUPPORT INTENT TAXONOMY SPECIFICATION
**Project:** Vireo Audio Support Intelligence  
**Phase:** Step 2 — AI-Assisted Ticket Classification & Taxonomy Engine  
**Author:** Senior AI Engineer & Support Operations Data Scientist  
**Date:** October 2026  

---

## 1. PURPOSE & ARCHITECTURAL PRINCIPLES

The legacy helpdesk system assigned tickets using a rigid intake chatbot based on initial customer responses. This resulted in severe queue misrouting (such as 100% of tickets mentioning "payment" or "money" being dumped into the Billing queue, regardless of whether the customer was complaining about a delayed package).

To establish an explainable, reproducible, and operationally aligned classification pipeline, Vireo Audio has established the **Seven-Pillar Support Intent Taxonomy**.

### Core Governance Rules:
1. **Separation of Intent vs. Routing:** Predicted issue category represents the *customer's underlying intent*. Predicted responsible team represents the *department best equipped to resolve it*. These two concepts are tracked as separate, independent fields.
2. **Zero Target Leakage:** The classification engine does NOT inspect `agent_id`, `site`, or `assigned_team`. Classification is derived solely from customer messages, agent resolution notes, and order/refund metadata signals.
3. **Deterministic & Explainable:** Every classification outputs traceable evidence strings and a calibrated heuristic confidence score. Ambiguous or low-signal cases explicitly flag `review_required = True`.

---

## 2. THE SEVEN-PILLAR SPECIFICATIONS

```
                            VIREO SUPPORT INTENT TAXONOMY
                                          │
       ┌──────────────────┬───────────────┴───────────────┬──────────────────┐
       │                  │                               │                  │
Order & Logistics    Returns & Refunds              Product & Tech     Billing & Invoicing
 (Logistics Team)    (Returns Desk)                 (Frontline T1)       (Billing Team)
                                                          │
                          ┌───────────────────────────────┴──────────────────┘
                          │                               │
                Hardware & Warranty              Account & Access
                (Escalations & Wty)               (Frontline T1)
```

---

### Pillar 1: Order & Logistics
- **Target Department:** `Logistics`
- **Description:** Fulfillment, shipping, courier handover, transit tracking, and physical delivery of orders.
- **Inclusion Criteria:**
  - Order tracking and live status inquiries (AWB, courier partner delays).
  - Delayed shipment or delivery past estimated arrival date.
  - Out-for-delivery, RTO (Return to Origin), or delivery attempt failures.
  - Shipment lost, stolen, or damaged in transit prior to customer receipt.
  - Delivery address correction, flat number typo, or incorrect pincode.
  - Incorrect product variant or missing accessories received inside the package.
- **Exclusion Criteria:**
  - Customer requesting return pickup after taking successful delivery (route to *Returns & Refunds*).
  - Duplicate payment or billing dispute with no delivery delay (route to *Billing & Invoicing*).
  - Hardware defect occurring days after successful unboxing (route to *Hardware & Warranty*).
- **Representative Examples:**
  - *"Paid on 19 Jun, still waiting for something to show up. Tracking says pending."*
  - *"My package has been out for delivery for 4 days now. Where is my courier?"*
  - *"Ordered Pulse 2 earbuds, but received a neckband inside the box."*
  - *"Courier says address incomplete. Need to update my pincode."*
- **Ambiguous Cases Requiring Review:**
  - Customer claims *"amount deducted, nothing at my door"*: classified as *Order & Logistics* if payment is confirmed and an order exists; classified as *Billing & Invoicing* if payment failed at gateway.
  - Package arrived crushed: classified as *Order & Logistics* if transit damage reported at delivery; classified as *Returns & Refunds* if customer initiates return pickup.

---

### Pillar 2: Returns & Refunds
- **Target Department:** `Returns Desk`
- **Description:** Post-delivery customer returns, reverse pickup logistics, warehouse QC inspection, and refund processing.
- **Inclusion Criteria:**
  - Customer-initiated return requests within the policy return window.
  - Reverse pickup scheduling, courier no-shows, or delayed pickup appointments.
  - Warehouse return receipt, physical inspection, and Quality Check (QC) status checks.
  - Refund status, approval, or credit timeline inquiries following a return.
  - Goodwill return authorizations approved by team leads.
- **Exclusion Criteria:**
  - Transit loss before first delivery (route to *Order & Logistics*).
  - Duplicate or gateway payment deductions with no return initiated (route to *Billing & Invoicing*).
  - Warranty replacement or RMA claim for in-warranty hardware faults (route to *Hardware & Warranty*).
- **Representative Examples:**
  - *"Courier has not arrived for the reverse pickup of my Strata 2 headphones."*
  - *"Returned the earbuds 5 days ago. When will my refund be credited?"*
  - *"Return pickup completed, but helpdesk shows QC inspection pending."*
  - *"I want to return this product and get my money back."*
- **Ambiguous Cases Requiring Review:**
  - Dead on Arrival (DOA) within 7 days: customer chooses full refund -> *Returns & Refunds*; customer chooses replacement unit -> *Hardware & Warranty*.

---

### Pillar 3: Billing & Invoicing
- **Target Department:** `Billing`
- **Description:** Financial transactions, payment gateway errors, duplicate debits, invoice requests, and tax documentation.
- **Inclusion Criteria:**
  - Duplicate transaction charges or double deduction for a single order.
  - Payment gateway failures, timeouts, or debited amounts without order confirmation.
  - Invoice generation, tax invoice download, or GSTIN updates on receipts.
  - Price adjustments, coupon application failures, or discount discrepancies.
  - Direct refund requests due to payment errors.
- **Exclusion Criteria:**
  - Confirmed paid orders that are delayed in transit (route to *Order & Logistics*).
  - Refunds arising from return of physical goods (route to *Returns & Refunds*).
  - Store credit issues resulting from SLA breaches (route to Frontline / Operations).
- **Representative Examples:**
  - *"I was charged twice on my credit card for order VR906763."*
  - *"Amount deducted from UPI but website gave an error and no order number was generated."*
  - *"Please provide a tax invoice with our company GSTIN number."*
  - *"The festive 15% discount code was not applied during checkout."*
- **Ambiguous Cases Requiring Review:**
  - Customer says *"money gone, no order"*: classify as *Billing & Invoicing* if no order exists in system; classify as *Order & Logistics* if order exists and is in fulfillment.

---

### Pillar 4: Technical & Firmware
- **Target Department:** `Chat/Email/Voice Frontline` (Tier 1)
- **Description:** Non-destructive troubleshooting, connectivity, Bluetooth pairing, companion mobile app, and firmware updates.
- **Inclusion Criteria:**
  - Bluetooth pairing failures, device discovery issues, or frequent disconnects.
  - Companion mobile app crashing, failing to sync, or feature toggles unresponsive.
  - Firmware update failures, frozen progress bar, or update loops.
  - Audio tuning, static noise, channel balance, latency, or microphone volume.
  - Battery optimization, charging case indicator troubleshooting, or soft resets.
- **Exclusion Criteria:**
  - Permanent physical hardware failure or dead components (route to *Hardware & Warranty*).
  - Account login OTP failures within the app (route to *Account & Access*).
  - Return requests due to dissatisfaction (route to *Returns & Refunds*).
- **Representative Examples:**
  - *"Left earbud connects but right earbud keeps dropping out."*
  - *"The Vireo app crashes immediately when I open equalizer settings."*
  - *"Firmware update is stuck at 42% for over an hour."*
  - *"Microphone volume is very muffled during calls."*
- **Ambiguous Cases Requiring Review:**
  - Device unresponsive: classify as *Technical & Firmware* if resolvable via soft reset SOP; classify as *Hardware & Warranty* if device is completely bricked or will not take a charge.

---

### Pillar 5: Hardware & Warranty
- **Target Department:** `Escalations & Warranty` (Tier 2 Certified)
- **Description:** Physical component failures, RMA claims, certified warranty repairs, and multi-touch hardware replacement.
- **Inclusion Criteria:**
  - Permanent hardware failure (no power, bricked after firmware, blown driver).
  - Single earbud completely silent despite verified factory reset.
  - Battery physical defects, swelling, or failure to charge past 0%.
  - Warranty claim status, RMA registration, or service center depot escalations.
  - Dead on Arrival (DOA) replacement unit dispatch under warranty.
- **Exclusion Criteria:**
  - Transient software or Bluetooth pairing glitches (route to *Technical & Firmware*).
  - Shipment transit damage reported at delivery (route to *Order & Logistics*).
  - Refund requests for returned goods (route to *Returns & Refunds*).
- **Representative Examples:**
  - *"Earbuds case does not power on at all, zero LED light with multiple cables."*
  - *"Warranty claim RMA82419 has been pending at the service center for 10 days."*
  - *"Right earbud is completely dead after water exposure despite IPX4 rating."*
  - *"Device bricked permanently during update. Need warranty replacement."*
- **Ambiguous Cases Requiring Review:**
  - Earbud silent: classify as *Technical & Firmware* if reset steps have not been attempted; classify as *Hardware & Warranty* if reset was verified and hardware failure confirmed.

---

### Pillar 6: Account & Access
- **Target Department:** `Chat/Email/Voice Frontline` (Tier 1)
- **Description:** Customer account management, authentication, credential recovery, and profile settings.
- **Inclusion Criteria:**
  - One-Time Password (OTP) not received on registered mobile number or email.
  - Customer account lockout or blocked access.
  - Updating registered phone number, email address, or shipping profile.
  - Password reset failures or session expiration loops.
- **Exclusion Criteria:**
  - Companion app crashing on device (route to *Technical & Firmware*).
  - Payment gateway OTP failures during checkout (route to *Billing & Invoicing*).
- **Representative Examples:**
  - *"I am locked out of my Vireo account and OTP is not arriving."*
  - *"Changed my phone number, need to update my registered account mobile."*
  - *"Login code never arrives on SMS. Tried 5 times."*
- **Ambiguous Cases Requiring Review:**
  - Customer mentions *"cannot login to buy"*: classify as *Account & Access* if the failure is credentials/OTP; classify as *Pre-Sales & Info* if inquiry is about purchase availability.

---

### Pillar 7: Pre-Sales & Info
- **Target Department:** `Chat/Email/Voice Frontline` (Tier 1)
- **Description:** Pre-purchase inquiries, device specifications, compatibility, warranty policies, and product guidance.
- **Inclusion Criteria:**
  - Product specifications, dimensions, battery runtime, and codec support.
  - Compatibility inquiries (iPhone, Android, Mac, Windows, Gaming consoles).
  - Water resistance, gym suitability, and IP rating explanations.
  - Product release dates, stock availability, and accessory compatibility.
- **Exclusion Criteria:**
  - Active troubleshooting of an already delivered item (route to *Technical & Firmware*).
  - Price disputes or coupon failures at checkout (route to *Billing & Invoicing*).
- **Representative Examples:**
  - *"Will the Strata 3 headphones work with an iPhone 15 over USB-C?"*
  - *"Can I swim or take a shower with the Pulse 2 earbuds?"*
  - *"Can I connect two Orbit smart speakers together for stereo sound?"*
  - *"What is the difference in battery life between Pulse and Pulse 2?"*
- **Ambiguous Cases Requiring Review:**
  - Customer asks *"can I exchange my old earbuds for new one"*: classify as *Pre-Sales & Info* if asking about trade-in policy; classify as *Returns & Refunds* if requesting return of purchased order.

---

## 3. RESPONSIBLE DEPARTMENT MAPPING LOGIC

Per Operating Policy v3.2 (§2 & §6), department routing is decoupled from category classification:

| Predicted Taxonomy Category | Assigned Department | Department Tier & Operating Scope |
| :--- | :--- | :--- |
| **Order & Logistics** | **Logistics** | Tier 1 Dedicated: Delivery tracking, courier partner re-dispatch, transit claims. |
| **Returns & Refunds** | **Returns Desk** | Tier 1 Dedicated: Reverse pickups, warehouse QC inspection, refund issuance. |
| **Billing & Invoicing** | **Billing** | Tier 1 Dedicated: Payment gateway disputes, duplicate debits, GST tax invoices. |
| **Hardware & Warranty** | **Escalations & Warranty** | Tier 2 Certified: Multi-touch RMA, service center liaison, replacement approval. |
| **Technical & Firmware** | **Chat / Email / Voice Frontline** | Tier 1 General: Routed by channel (Chat/Social -> Chat FL; Email -> Email FL; Voice -> Voice FL). |
| **Account & Access** | **Chat / Email / Voice Frontline** | Tier 1 General: Profile authentication, OTP resent, credential unlocking. |
| **Pre-Sales & Info** | **Chat / Email / Voice Frontline** | Tier 1 General: Spec sheets, compatibility guidance, feature explanations. |
