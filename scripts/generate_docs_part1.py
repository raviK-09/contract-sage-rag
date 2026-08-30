import os
from fpdf import FPDF

class LegalPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, "STRICTLY CONFIDENTIAL & PRIVILEGED", align="R", new_x="LMARGIN", new_y="NEXT")

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", align="C")

    def add_title(self, text):
        self.set_font("helvetica", "B", 16)
        self.multi_cell(0, 10, text, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def add_subtitle(self, text):
        self.set_font("helvetica", "B", 12)
        self.multi_cell(0, 8, text, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def add_preamble(self, text):
        self.set_font("helvetica", "", 10)
        self.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def add_clause_heading(self, number, title):
        self.set_font("helvetica", "B", 11)
        self.multi_cell(0, 8, f"{number}. {title}", new_x="LMARGIN", new_y="NEXT")

    def add_clause_text(self, text):
        self.set_font("helvetica", "", 10)
        self.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(3)

    def add_subclause(self, number, text):
        self.set_font("helvetica", "", 10)
        indent = 25
        self.set_x(indent)
        w = self.w - indent - self.r_margin
        self.multi_cell(w, 5, f"{number} {text}", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def add_schedule_heading(self, title):
        self.add_page()
        self.set_font("helvetica", "B", 14)
        self.multi_cell(0, 10, title, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def add_signature_block(self, parties):
        self.ln(10)
        self.set_font("helvetica", "B", 10)
        self.multi_cell(0, 5, "IN WITNESS WHEREOF, the Parties hereto have executed this Agreement on the day and year first above written.")
        self.ln(15)
        
        y_pos = self.get_y()
        
        for i, party in enumerate(parties):
            if i % 2 == 0:
                self.set_xy(10, y_pos)
            else:
                self.set_xy(110, y_pos)
                
            self.cell(80, 5, "___________________________", ln=True)
            if i % 2 == 0:
                self.set_x(10)
            else:
                self.set_x(110)
            self.cell(80, 5, party['role'], ln=True)
            if i % 2 == 0:
                self.set_x(10)
            else:
                self.set_x(110)
            self.cell(80, 5, f"Name: {party['name']}", ln=True)
            if i % 2 == 0:
                self.set_x(10)
            else:
                self.set_x(110)
            self.cell(80, 5, "Date: _____________________", ln=True)
            
            if i % 2 != 0 or i == len(parties) - 1:
                y_pos = self.get_y() + 15
                
        self.ln(15)
        self.set_font("helvetica", "B", 10)
        self.cell(0, 5, "WITNESSES:", ln=True)
        self.ln(10)
        
        y_pos = self.get_y()
        
        for i in range(2):
            if i % 2 == 0:
                self.set_xy(10, y_pos)
            else:
                self.set_xy(110, y_pos)
                
            self.cell(80, 5, f"{i+1}. _________________________", ln=True)
            if i % 2 == 0:
                self.set_x(10)
            else:
                self.set_x(110)
            self.cell(80, 5, "Name: _____________________", ln=True)
            if i % 2 == 0:
                self.set_x(10)
            else:
                self.set_x(110)
            self.cell(80, 5, "Address: ___________________", ln=True)
        self.ln(10)

    def add_separator(self):
        self.ln(5)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)


def generate_residential_agreement(output_dir):
    pdf = LegalPDF()
    pdf.add_page()
    pdf.add_title("RESIDENTIAL RENTAL AGREEMENT")
    
    preamble = (
        "This Residential Rental Agreement (\"Agreement\") is made and executed at Bangalore on this "
        "1st day of September, 2025, BY AND BETWEEN:\n\n"
        "Mr. Rajesh Kumar Sharma, S/o Late Shri Ramesh Chandra Sharma, aged about 58 years, residing at "
        "House No. 42, 2nd Main Road, Jayanagar 4th Block, Bangalore - 560041, holding PAN: ABCPS1234A "
        "(hereinafter referred to as the \"Landlord\", which expression shall, unless it be repugnant to the context "
        "or meaning thereof, mean and include his heirs, legal representatives, executors, administrators, and assigns) "
        "OF THE ONE PART;\n\n"
        "AND\n\n"
        "Ms. Priya Nair, D/o Shri Gopalakrishnan Nair, aged about 28 years, employed at Infosys Technologies Limited, "
        "currently residing at Flat 105, Sunrise Apartments, Electronic City, Bangalore - 560100, holding PAN: DEFPN5678B "
        "(hereinafter referred to as the \"Tenant\", which expression shall, unless it be repugnant to the context or meaning "
        "thereof, mean and include her heirs, legal representatives, executors, and administrators) OF THE OTHER PART.\n\n"
        "WHEREAS the Landlord is the absolute owner of the property bearing Flat No. 302, 3rd Floor, 'Lakshmi Residency', "
        "#18/2, 1st Cross Road, Koramangala 5th Block, Bangalore - 560095, comprising 2 bedrooms, 1 hall, kitchen, 2 bathrooms, "
        "and 1 balcony, with a total carpet area of approximately 1,100 square feet (hereinafter referred to as the 'Premises'). "
        "AND WHEREAS the Tenant has approached the Landlord to grant a lease of the Premises for residential purposes, and the "
        "Landlord has agreed to grant the same on the terms and conditions set forth herein below."
    )
    pdf.add_preamble(preamble)
    
    pdf.add_clause_heading("1", "DEFINITIONS")
    pdf.add_clause_text("In this Agreement, unless the context otherwise requires, the following expressions shall have the following meanings:")
    definitions = [
        "\"Agreement\" means this Residential Rental Agreement including all schedules, annexures, and amendments hereto executed in writing by both Parties.",
        "\"Common Areas\" means those parts of Lakshmi Residency intended for common use by all residents, including corridors, staircases, elevators, lobby, parking areas, and club house.",
        "\"Fixtures\" means all electrical, plumbing, sanitary fittings, woodwork, appliances, and other installations provided by the Landlord as detailed in Schedule B.",
        "\"Force Majeure Event\" means any event beyond the reasonable control of the Parties including but not limited to acts of God, fire, flood, pandemic, government lockdowns, or riots.",
        "\"Landlord\" means Mr. Rajesh Kumar Sharma and includes his authorized representatives.",
        "\"Maintenance Charges\" means the monthly sum payable to the Society for upkeep of Common Areas.",
        "\"Premises\" means Flat No. 302 as more fully described in Schedule A.",
        "\"Security Deposit\" means the interest-free refundable deposit paid by the Tenant to the Landlord.",
        "\"Society\" means the registered welfare association or management committee of Lakshmi Residency.",
        "\"Tenant\" means Ms. Priya Nair.",
        "\"Utilities\" means electricity, water, gas, internet, and any other similar services consumed at the Premises."
    ]
    for i, defn in enumerate(definitions):
        pdf.add_subclause(f"1.{i+1}", defn)

    pdf.add_clause_heading("2", "TERM OF LEASE")
    pdf.add_clause_text("The term of this lease shall be for a period of 11 (Eleven) months commencing from the 1st day of September, 2025. Upon expiry of this initial term, the lease may be renewed for a further period by mutual written agreement between the Parties, subject to a mandatory 10% (Ten Percent) enhancement in the monthly rent. The Parties agree to a strict lock-in period of 6 (Six) months from the commencement date, during which neither party shall have the right to terminate this Agreement without cause, except as otherwise explicitly provided herein.")

    pdf.add_clause_heading("3", "RENT")
    pdf.add_clause_text("The Tenant shall pay a monthly rent of Rs. 28,000/- (Rupees Twenty Eight Thousand only) for the use and occupation of the Premises. The rent shall be payable in advance on or before the 5th day of each calendar month via electronic bank transfer to the Landlord's designated bank account. The Tenant is granted a grace period of 7 (Seven) days, following which a late payment fee of Rs. 150/- (Rupees One Hundred and Fifty only) per day shall be levied until the date of actual realization. As collateral security, the Tenant has handed over 11 post-dated cheques corresponding to the monthly rent amounts, receipt of which the Landlord hereby acknowledges.")

    pdf.add_clause_heading("4", "SECURITY DEPOSIT")
    pdf.add_clause_text("The Tenant has paid to the Landlord an interest-free refundable Security Deposit of Rs. 2,80,000/- (Rupees Two Lakhs Eighty Thousand only), equivalent to 10 months' rent, via NEFT on 28th August 2025. The Landlord hereby acknowledges receipt of the same. This Security Deposit shall not bear any interest and shall be refunded to the Tenant within 60 (Sixty) days of the Tenant vacating the Premises and handing over peaceful possession. The Landlord reserves the absolute right to deduct from this deposit any arrears of rent, unpaid utility bills, society maintenance dues, and the cost of repairing any damages to the Premises or Fixtures beyond normal wear and tear.")

    pdf.add_clause_heading("5", "MAINTENANCE AND REPAIRS")
    pdf.add_clause_text("The Tenant shall keep the Premises in a clean, hygienic, and habitable condition. The Tenant shall be solely responsible for minor day-to-day repairs, including replacement of bulbs, fixing minor plumbing leaks, and hardware adjustments, up to a maximum cost of Rs. 5,000/- (Rupees Five Thousand only) per instance. The Landlord shall be responsible for all major structural repairs, major electrical faults, and seepage issues not caused by the Tenant's negligence. The Tenant must report any requirement for major repairs in writing to the Landlord within 48 (Forty-Eight) hours of discovery. Furthermore, the Tenant agrees to bear the cost of the annual servicing of the air conditioning units installed in the Premises.")

    pdf.add_clause_heading("6", "UTILITIES AND CHARGES")
    pdf.add_clause_text("In addition to the monthly rent, the Tenant shall pay all utility charges on actuals. Electricity charges shall be paid directly to BESCOM based on the meter readings. Water charges are fixed at Rs. 500/- (Rupees Five Hundred only) per month, payable along with the rent. The Tenant shall directly pay the piped gas connection bills and internet broadband subscriptions. Furthermore, the Tenant agrees to pay the monthly society maintenance charges of Rs. 4,500/- (Rupees Four Thousand Five Hundred only) directly to the Society's bank account before the 10th of every month and provide proof of payment to the Landlord upon request.")

    pdf.add_clause_heading("7", "USE OF PREMISES")
    pdf.add_clause_text("The Tenant covenants to use the Premises strictly and exclusively for residential purposes for herself and her immediate family, not exceeding a maximum of 4 (Four) occupants. The Tenant shall not use or permit the use of the Premises for any commercial, illegal, or immoral activities. Subletting, assigning, or parting with the possession of the Premises, either in whole or in part, is strictly prohibited and shall constitute a material breach. The Tenant is not permitted to keep any pets exceeding 10 kg in body weight. Smoking within the Common Areas of the building is strictly forbidden.")

    pdf.add_clause_heading("8", "LANDLORD'S RIGHT OF ACCESS")
    pdf.add_clause_text("The Landlord or his authorized representatives shall have the right to enter and inspect the Premises, or to carry out necessary repairs, provided a minimum of 24 (Twenty-Four) hours advance written notice is given to the Tenant. Such inspections shall be conducted only during reasonable hours, specifically between 10:00 AM and 6:00 PM. Notwithstanding the foregoing, advance notice shall not be required in the event of an emergency, which is broadly defined to include, but is not limited to, severe water leakage, fire outbreaks, immediate security concerns, or reasonable suspicion of a material breach of this Agreement.")

    pdf.add_clause_heading("9", "MODIFICATIONS AND ALTERATIONS")
    pdf.add_clause_text("The Tenant shall not make any structural additions, modifications, or alterations to the Premises, nor drill holes into the masonry or woodwork, without the prior written consent of the Landlord. If any such modifications are permitted, the entire cost shall be borne by the Tenant. Upon the termination or expiration of this Agreement, the Landlord may, at his sole discretion, require the Tenant to restore the Premises to its original condition at the Tenant's expense. Any permanent fixtures or improvements installed by the Tenant that cannot be removed without causing damage shall become the absolute property of the Landlord without any compensation to the Tenant.")

    pdf.add_clause_heading("10", "PARKING")
    pdf.add_clause_text("The Tenant is allocated one designated covered car parking spot numbered B-302 in the basement of the building. This parking spot shall be used solely for parking private passenger vehicles belonging to the Tenant. The parking of commercial vehicles, derelict vehicles, or the carrying out of vehicular repairs (other than emergency tire changes) in the parking area is strictly prohibited. The use of visitor parking spaces shall be strictly governed by the rules and regulations formulated by the Society.")

    pdf.add_clause_heading("11", "SOCIETY RULES AND REGULATIONS")
    pdf.add_clause_text("The Tenant unconditionally agrees to abide by all the bylaws, rules, and regulations set forth by the Society of Lakshmi Residency, as amended from time to time. The Tenant shall observe quiet hours from 10:00 PM to 7:00 AM, ensuring no nuisance or disturbance is caused to neighboring residents. Mandatory waste segregation into wet, dry, and hazardous waste as per BBMP guidelines and Society rules must be strictly followed. Any fines or penalties levied by the Society or municipal authorities due to the Tenant's non-compliance shall be borne entirely and promptly by the Tenant.")

    pdf.add_clause_heading("12", "INSURANCE")
    pdf.add_clause_text("The Tenant acknowledges that she is solely responsible for obtaining and maintaining adequate insurance coverage for all her personal belongings, furniture, and valuables kept within the Premises. The Landlord shall maintain comprehensive structural insurance for the building and the Premises. However, the Tenant shall be held fully liable to compensate the Landlord or the Society for any damage caused to the Premises or the Common Areas arising out of the Tenant's negligence or willful misconduct, or that of her guests.")

    pdf.add_clause_heading("13", "TERMINATION")
    pdf.add_clause_text("Following the expiry of the 6-month lock-in period, either party may terminate this Agreement by serving a 2 (Two) months prior written notice upon the other. The Landlord reserves the right to terminate this Agreement immediately and demand immediate possession if the Tenant defaults on rent payment for a period exceeding 30 (Thirty) days, engages in illegal activities, or commits a material breach of any terms herein. If the Tenant vacates the Premises during the lock-in period without lawful cause, she shall forfeit the entire Security Deposit. Conversely, if the Landlord terminates this Agreement during the lock-in period without cause, he shall be liable to pay the Tenant a sum equivalent to double the Security Deposit.")

    pdf.add_clause_heading("14", "HANDOVER AND VACATING")
    pdf.add_clause_text("Upon the expiration or earlier termination of this Agreement, the Tenant shall hand over peaceful and vacant possession of the Premises in the same condition as it was received, ordinary wear and tear excepted. The Tenant must ensure the Premises undergoes professional deep cleaning prior to handover. The Tenant shall surrender all sets of keys, access cards, and parking stickers to the Landlord. Furthermore, the Tenant must provide proof of settlement of all utility bills and Society dues up to the date of vacating, and provide a forwarding address for future correspondence.")

    pdf.add_clause_heading("15", "GOVERNING LAW AND JURISDICTION")
    pdf.add_clause_text("This Agreement shall be governed by, construed, and interpreted in accordance with the laws of India, specifically including the Karnataka Rent Control Act 2001, the Indian Contract Act 1872, and the Transfer of Property Act 1882, as applicable. Subject to the dispute resolution clause herein, the courts of competent jurisdiction located in Bangalore shall have exclusive jurisdiction to entertain any suits, actions, or proceedings arising out of or in connection with this Agreement.")

    pdf.add_clause_heading("16", "DISPUTE RESOLUTION")
    pdf.add_clause_text("In the event of any dispute, difference, or claim arising out of or relating to this Agreement, the Parties shall first attempt to resolve the matter amicably through good faith negotiations for a period of 30 (Thirty) days. If unresolved, the dispute shall be referred to mediation under the provisions of the Mediation Act. Should mediation fail, the dispute shall be finally settled by a sole arbitrator appointed mutually under the provisions of the Arbitration and Conciliation Act 1996. The arbitration proceedings shall be conducted in the English language, the seat of arbitration shall be Bangalore, and the costs shall be shared equally by both Parties.")

    pdf.add_clause_heading("17", "INDEMNIFICATION")
    pdf.add_clause_text("The Tenant hereby agrees to indemnify, defend, and hold harmless the Landlord from and against any and all claims, demands, liabilities, damages, losses, costs, and expenses (including reasonable legal fees) asserted by any third party arising out of or resulting from the Tenant's use or occupancy of the Premises, any breach of this Agreement by the Tenant, or any negligent act or omission by the Tenant or her guests.")

    pdf.add_clause_heading("18", "FORCE MAJEURE")
    pdf.add_clause_text("Neither Party shall be held liable for any failure or delay in fulfilling their respective obligations under this Agreement (except for the payment of rent and dues) if such failure or delay is caused by a Force Majeure Event, including natural disasters, pandemics, or government orders. During the continuance of a Force Majeure Event that renders the Premises uninhabitable, the obligations of this Agreement shall be suspended. If the Force Majeure Event continues for a continuous period exceeding 90 (Ninety) days, either Party may terminate this Agreement without penalty.")

    pdf.add_clause_heading("19", "NOTICES")
    pdf.add_clause_text("All notices, demands, or other communications required or permitted to be given under this Agreement shall be in writing. Such notices shall be deemed to have been duly given if delivered personally, sent by registered post with acknowledgment due, sent by recognized national courier, or transmitted via email to the addresses specified in the preamble or Schedule C. Notices sent by post or courier shall be deemed received 3 (Three) days after the date of dispatch.")

    pdf.add_clause_heading("20", "MISCELLANEOUS")
    pdf.add_clause_text("This Agreement constitutes the entire understanding between the Parties concerning the subject matter hereof and supersedes all prior agreements, understandings, or representations, oral or written. No amendment or modification to this Agreement shall be valid unless made in writing and signed by both Parties. If any provision is held to be invalid or unenforceable, the remaining provisions shall remain in full force and effect. The failure to enforce any right shall not constitute a waiver. This Agreement may be executed in counterparts, each of which shall be deemed an original.")

    pdf.add_schedule_heading("SCHEDULE A: DESCRIPTION OF THE PREMISES")
    pdf.add_clause_text("All that piece and parcel of the residential apartment bearing Flat No. 302, situated on the 3rd Floor of the building known as 'Lakshmi Residency', located at #18/2, 1st Cross Road, Koramangala 5th Block, Bangalore - 560095, comprising:")
    pdf.add_clause_text("- Master Bedroom: 14 ft x 12 ft with attached bathroom (8 ft x 5 ft)")
    pdf.add_clause_text("- Guest Bedroom: 12 ft x 11 ft")
    pdf.add_clause_text("- Living/Dining Hall: 22 ft x 14 ft")
    pdf.add_clause_text("- Kitchen: 10 ft x 8 ft with utility area")
    pdf.add_clause_text("- Common Bathroom: 7 ft x 5 ft")
    pdf.add_clause_text("- Balcony: 10 ft x 4 ft attached to the living hall")
    pdf.add_clause_text("Bounded on the East by: Open space and road; West by: Flat No. 303; North by: Corridor; South by: Property No. 19.")

    pdf.add_schedule_heading("SCHEDULE B: INVENTORY OF FIXTURES AND FITTINGS")
    pdf.add_clause_text("The following fixtures and fittings are provided by the Landlord in good working condition:")
    pdf.add_clause_text("1. Ceiling Fans (Crompton) - 4 Nos. (Living room, both bedrooms, kitchen)")
    pdf.add_clause_text("2. LED Tube Lights (Philips) - 8 Nos.")
    pdf.add_clause_text("3. Split Air Conditioners 1.5 Ton (Daikin) - 2 Nos. (In bedrooms)")
    pdf.add_clause_text("4. Geysers 15L (AO Smith) - 2 Nos. (In both bathrooms)")
    pdf.add_clause_text("5. Modular Kitchen woodwork with Hettich channels")
    pdf.add_clause_text("6. Chimney (Faber) - 1 No.")
    pdf.add_clause_text("7. Built-in Wardrobes - 2 Sets (One in each bedroom)")
    pdf.add_clause_text("8. Bathroom mirrors and health faucets - 2 Sets")
    pdf.add_clause_text("9. Curtain rods installed in all windows and balcony door")
    pdf.add_clause_text("10. Main door safety grill and Godrej interlock")
    pdf.add_clause_text("Condition: All items are handed over in fully functional condition without any defects.")

    pdf.add_schedule_heading("SCHEDULE C: CONTACT INFORMATION")
    pdf.add_clause_text("Landlord Contact:")
    pdf.add_clause_text("Mobile: +91-9876543210")
    pdf.add_clause_text("Email: rajesh.sharma42@email.com")
    pdf.ln(5)
    pdf.add_clause_text("Tenant Contact:")
    pdf.add_clause_text("Mobile: +91-9988776655")
    pdf.add_clause_text("Email: priya.nair.infosys@email.com")
    pdf.ln(5)
    pdf.add_clause_text("Emergency Society Contact:")
    pdf.add_clause_text("Estate Manager: Mr. Venkat Rao (Mobile: +91-8899001122)")

    parties = [
        {"role": "LANDLORD", "name": "Rajesh Kumar Sharma"},
        {"role": "TENANT", "name": "Priya Nair"}
    ]
    pdf.add_signature_block(parties)

    output_path = os.path.join(output_dir, "residential_rental_agreement.pdf")
    pdf.output(output_path)
    return pdf.page_no()

def generate_employment_agreement(output_dir):
    pdf = LegalPDF()
    pdf.add_page()
    pdf.add_title("EMPLOYMENT AGREEMENT")
    
    preamble = (
        "This Employment Agreement (\"Agreement\") is made and entered into on this 15th day of October, 2025, "
        "at Bangalore, BY AND BETWEEN:\n\n"
        "NovaTech Solutions Private Limited, a company incorporated under the Companies Act, 2013, bearing "
        "CIN: U72200KA2019PTC128456, and having its Registered Office at 5th Floor, Tower B, Prestige Tech Park, "
        "Outer Ring Road, Marathahalli, Bangalore - 560037 (hereinafter referred to as the \"Company\", which "
        "expression shall, unless repugnant to the context or meaning thereof, mean and include its successors, "
        "affiliates, and permitted assigns) OF THE FIRST PART;\n\n"
        "AND\n\n"
        "Mr. Amit Kumar Verma, S/o Shri Rakesh Kumar Verma, bearing PAN: GHIPV2345C and Aadhaar No: 9876 5432 1098, "
        "residing at Flat 804, Brigade Gateway, Rajajinagar, Bangalore - 560055 (hereinafter referred to as the "
        "\"Employee\", which expression shall, unless repugnant to the context or meaning thereof, mean and include "
        "his legal heirs, executors, and administrators) OF THE SECOND PART.\n\n"
        "The Company and the Employee are hereinafter individually referred to as a 'Party' and collectively as the 'Parties'."
    )
    pdf.add_preamble(preamble)

    pdf.add_clause_heading("1", "DEFINITIONS")
    pdf.add_clause_text("In this Agreement, the capitalized terms shall have the following meanings:")
    definitions = [
        "\"Affiliates\" means any entity that directly or indirectly controls, is controlled by, or is under common control with the Company.",
        "\"Board\" means the Board of Directors of NovaTech Solutions Private Limited.",
        "\"CTC\" means Cost to Company, encompassing all fixed, variable, and statutory components of compensation.",
        "\"Company\" means NovaTech Solutions Private Limited.",
        "\"Confidential Information\" means all non-public information relating to the Company's business, technology, and finances.",
        "\"Effective Date\" means the 15th of October, 2025.",
        "\"Employee\" means Mr. Amit Kumar Verma.",
        "\"ESOP\" means the Employee Stock Option Plan 2023 of the Company.",
        "\"Group Companies\" means the Company and all its Affiliates globally.",
        "\"Intellectual Property\" means patents, copyrights, trademarks, trade secrets, software code, and inventions.",
        "\"Notice Period\" means the statutory or contractual duration required to be served prior to termination of employment.",
        "\"Probation Period\" means the initial assessment period of employment.",
        "\"Separation Date\" means the final day of employment following the fulfillment of all exit formalities.",
        "\"Variable Pay\" means the performance-linked component of the compensation structure.",
        "\"Work Product\" means all deliverables, code, designs, and documentation created by the Employee during the course of employment."
    ]
    for i, defn in enumerate(definitions):
        pdf.add_subclause(f"1.{i+1}", defn)

    pdf.add_clause_heading("2", "APPOINTMENT AND DESIGNATION")
    pdf.add_clause_text("Subject to the terms and conditions set forth herein, the Company hereby appoints the Employee to the position of Senior Software Engineer - Level 5, within the Engineering Division, specifically assigned to the AI/ML Platform Team. The employment shall commence on the Effective Date of 15th October 2025. The Employee accepts this appointment and agrees to diligently perform the duties and responsibilities associated with this designation, as well as any other tasks assigned by the Company from time to time.")

    pdf.add_clause_heading("3", "PROBATION PERIOD")
    pdf.add_clause_text("The Employee shall be on probation for a period of 6 (Six) months commencing from the Effective Date. The Company reserves the right, at its sole discretion, to extend this probation period by an additional 3 (Three) months if the Employee's performance is found lacking. During the probation period (including any extensions), either Party may terminate this Agreement by providing 15 (Fifteen) days prior written notice to the other Party, without assigning any reasons. Confirmation of employment shall be strictly subject to a satisfactory performance review at the end of the probation period, which will be communicated in writing.")

    pdf.add_clause_heading("4", "COMPENSATION AND BENEFITS")
    pdf.add_subclause("4.1", "Annual CTC: The Employee's total Annual CTC shall be Rs. 24,00,000/- (Rupees Twenty Four Lakhs only), structured as follows: Basic Salary: Rs. 9,60,000/- (40%); House Rent Allowance: Rs. 4,80,000/- (20%); Special Allowance: Rs. 4,32,000/- (18%); Employer PF Contribution: Rs. 1,15,200/-; Medical Insurance Premium: Rs. 72,000/-; Gratuity (notional): Rs. 46,154/-; Other Benefits: Rs. 94,646/-.")
    pdf.add_subclause("4.2", "Variable Pay: The Employee shall be eligible for a Variable Pay of Rs. 4,00,000/- per annum. This payout is strictly linked to individual performance (60% weightage) and company performance (40% weightage). It shall be paid quarterly in arrears and will be pro-rated for any partial quarters served.")
    pdf.add_subclause("4.3", "ESOP Grant: The Employee is granted 800 stock options at an exercise price of Rs. 10/- per share. These options are subject to a 4-year vesting schedule with a 1-year cliff (25% vesting after 1 year, followed by 6.25% per quarter thereafter), strictly governed by the terms of the ESOP Plan 2023.")
    pdf.add_subclause("4.4", "Joining Bonus: A one-time joining bonus of Rs. 1,50,000/- shall be paid with the first month's salary. This amount is subject to complete clawback if the Employee resigns within 12 months of the Effective Date.")
    pdf.add_subclause("4.5", "Relocation Allowance: The Company shall reimburse one-time relocation expenses up to Rs. 50,000/- upon submission of valid receipts.")

    pdf.add_clause_heading("5", "WORKING HOURS AND ATTENDANCE")
    pdf.add_clause_text("The standard working hours of the Company are from 9:30 AM to 6:30 PM, Monday through Friday. However, given the exempt nature of the role, the Employee acknowledges that reasonable additional hours may be required to meet project deadlines without any entitlement to extra compensation or overtime pay. The Company offers a flexible work-from-home policy allowing up to 2 (Two) days per week of remote work, strictly subject to the reporting manager's prior approval. All daily attendance must be accurately marked via the Company's centralized HR portal.")

    pdf.add_clause_heading("6", "LEAVE POLICY")
    pdf.add_clause_text("In accordance with the Company's leave policy, the Employee is entitled to 28 Privilege Leaves (PL), 12 Sick/Casual Leaves, and 3 Personal Leaves per calendar year, pro-rated for the year of joining, along with 12 declared public holidays. Unused Privilege Leaves may be encashed up to a maximum of 10 days at the end of the financial year. The granting of Leave Without Pay is entirely at the Company's discretion. Maternity and paternity benefits shall be provided strictly in accordance with applicable statutory laws.")

    pdf.add_clause_heading("7", "EMPLOYEE BENEFITS")
    pdf.add_clause_text("The Employee shall be enrolled in the Company's Group Medical Insurance policy, providing a cover of Rs. 10,00,000/- extending to the Employee, spouse, and up to 2 dependent children. Additionally, the Employee shall be covered by a Group Term Life Insurance policy equivalent to 3x their annual CTC, and a Group Personal Accident Insurance policy with a cover of Rs. 50,00,000/-. The Employee is also entitled to an annual comprehensive health checkup funded by the Company.")

    pdf.add_clause_heading("8", "DUTIES AND RESPONSIBILITIES")
    pdf.add_clause_text("The Employee is expected to perform all assigned duties diligently, ethically, and to the best of their abilities. The Employee must adhere to all lawful instructions from superiors, devote their full working time and attention to the Company's business, and maintain the highest professional standards. The Employee shall initially report to the VP of Engineering, or to any other executive as designated by the Company from time to time.")

    pdf.add_clause_heading("9", "WORK LOCATION AND TRANSFER")
    pdf.add_clause_text("The primary work location for the Employee shall be the Company's office in Bangalore. However, the Employee acknowledges that the role may require temporary domestic or international travel. Furthermore, the Company reserves the absolute right to transfer or depute the Employee to any other office, project site, affiliate, or subsidiary located anywhere in India or abroad, by providing 30 (Thirty) days advance notice. A refusal to accept such a transfer shall constitute a material breach of this Agreement.")

    pdf.add_clause_heading("10", "INTELLECTUAL PROPERTY ASSIGNMENT")
    pdf.add_clause_text("The Employee unconditionally agrees that ALL work product, inventions, ideas, code, algorithms, designs, and documentation created: (a) during the term of employment, (b) using the Company's resources, time, or facilities, or (c) related in any way to the Company's current or anticipated business, shall belong exclusively and perpetually to the Company. The Employee undertakes to promptly execute any documents required to perfect the Company's title to such Intellectual Property. The Employee explicitly waives all moral rights in the Work Product to the fullest extent permitted by law. This assignment explicitly INCLUDES ideas or inventions conceived outside standard working hours if they relate to the Company's business domain. The Employee is strictly obligated to disclose all such inventions to the Company within 30 days of conception.")

    pdf.add_clause_heading("11", "CONFIDENTIALITY")
    pdf.add_clause_text("Confidential Information is defined broadly and includes, but is not limited to, source code, proprietary algorithms, business plans, customer and prospect lists, pricing strategies, financial data, employee data, trade secrets, know-how, processes, AND any other information marked as confidential or reasonably understood to be confidential by its nature. The Employee shall maintain strict confidentiality and shall not disclose, copy, reverse engineer, or derive works from any Confidential Information. These confidentiality obligations are absolute and shall survive for a period of 36 (Thirty-Six) months following the termination of employment.")

    pdf.add_clause_heading("12", "NON-COMPETE RESTRICTION")
    pdf.add_clause_text("During the term of employment and for a period of 12 (Twelve) months immediately following the cessation of employment for any reason, within the geographical territory of India, the Employee shall not directly or indirectly join, establish, advise, or hold any interest in any business entity that is in direct competition with the Company's AI/ML platform products and services. The Employee acknowledges that this restriction is reasonable and necessary to protect the Company's legitimate business interests. The Company may, at its sole discretion, waive this clause in writing.")

    pdf.add_clause_heading("13", "NON-SOLICITATION")
    pdf.add_clause_text("The Employee covenants that during employment and for a period of 18 (Eighteen) months post-employment, they shall not, directly or indirectly: (a) solicit, induce, or attempt to hire any employee, consultant, or contractor of the Company or its Affiliates; or (b) solicit, divert, or attempt to divert the business of any client, customer, or vendor with whom the Employee had direct contact or material dealings during the last 24 (Twenty-Four) months of their employment with the Company.")

    pdf.add_clause_heading("14", "CONFLICT OF INTEREST AND MOONLIGHTING")
    pdf.add_clause_text("The Employee shall exclusively dedicate their professional efforts to the Company. The Employee is strictly prohibited from engaging in any outside employment, independent consulting, advisory roles, or freelance work, whether paid or unpaid, without prior written approval from the Head of HR. The Employee shall not hold any directorship or partnership in any other entity. The Employee must immediately disclose any existing or potential conflicts of interest. Contributions to open-source projects are permitted only if they are entirely unrelated to the Company's Intellectual Property, do not utilize Company resources, and are undertaken strictly outside working hours.")

    pdf.add_clause_heading("15", "CODE OF CONDUCT")
    pdf.add_clause_text("The Employee is required to strictly comply with all Company policies, procedures, and manuals, as amended from time to time. This includes, but is not limited to, absolute adherence to the anti-bribery and anti-corruption policies, data protection regulations, the social media acceptable use policy, and policies preventing sexual harassment at the workplace. The Company maintains a robust whistleblower protection policy to report any unethical practices without fear of retaliation.")

    pdf.add_clause_heading("16", "TERMINATION")
    pdf.add_subclause("16.1", "By Company without cause: The Company may terminate this Agreement without assigning any cause by providing 90 (Ninety) days prior written notice, or by paying basic salary in lieu of the unserved notice period.")
    pdf.add_subclause("16.2", "By Employee: The Employee may resign by providing 90 (Ninety) days written notice. The Company reserves the right to waive this notice period partly or fully, or to place the Employee on garden leave.")
    pdf.add_subclause("16.3", "For Cause: The Company may terminate the employment immediately, without notice or severance, for cause. 'Cause' includes fraud, dishonesty, gross misconduct, material breach of this Agreement, conviction of a criminal offence, repeated underperformance following two formal Performance Improvement Plans (PIPs), unauthorized disclosure of Confidential Information, or substance abuse at the workplace.")
    pdf.add_subclause("16.4", "Effect of Termination: Upon termination, the Employee must return all Company property (laptops, badges, documents) within 3 working days, complete a comprehensive knowledge transfer, and participate in a mandatory exit interview. The Employee must refrain from making any negative or disparaging commentary about the Company.")
    pdf.add_subclause("16.5", "Variable Pay and Bonus Clawback: Any Variable Pay, joining bonus, or performance bonus received by the Employee in the preceding 12 months must be refunded in full to the Company if the Employee resigns within 6 months of the payout date, or is terminated for cause.")
    pdf.add_subclause("16.6", "ESOP: All unvested stock options shall lapse immediately upon the Separation Date. Vested options may be exercised in accordance with the ESOP Plan terms, generally within a 90-day exercise window post-separation.")
    pdf.add_subclause("16.7", "Garden Leave: The Company may, at its absolute discretion, place the Employee on garden leave during the notice period with full pay and benefits. During this period, the Employee is not required to attend work but must remain reasonably available for queries and handover.")

    pdf.add_clause_heading("17", "GOVERNING LAW AND JURISDICTION")
    pdf.add_clause_text("This Agreement, its interpretation, performance, and enforcement, shall be governed exclusively by the laws of India. Subject to the arbitration clause, the courts of competent jurisdiction located in Bangalore shall have exclusive jurisdiction over any matters or disputes arising under or in connection with this Agreement.")

    pdf.add_clause_heading("18", "ARBITRATION")
    pdf.add_clause_text("Any dispute, controversy, or claim arising out of or relating to this Agreement, or the breach, termination, or invalidity thereof, shall be referred to and finally resolved by arbitration. The arbitral tribunal shall consist of a sole arbitrator mutually appointed by the Parties. If the Parties fail to agree on an arbitrator within 30 days, the appointment shall be made by the Bangalore International Mediation Arbitration and Conciliation Centre. The arbitration shall be governed by the Arbitration and Conciliation Act 1996. The language of arbitration shall be English, and the legal seat and venue of arbitration shall be Bangalore. The arbitrator's decision shall be final and binding on both Parties.")

    pdf.add_clause_heading("19", "AMENDMENT")
    pdf.add_clause_text("No amendment, modification, or waiver of any provision of this Agreement shall be valid or binding unless it is made in writing and duly signed by authorized representatives of both Parties. The Parties explicitly agree that no oral modifications shall have any legal effect.")

    pdf.add_clause_heading("20", "SEVERABILITY, ENTIRE AGREEMENT, COUNTERPARTS")
    pdf.add_clause_text("If any provision of this Agreement is found by a court or arbitrator to be invalid or unenforceable, such invalidity shall not affect the remaining provisions, which shall remain in full force. This Agreement constitutes the entire agreement between the Parties and supersedes all prior discussions, offer letters, and understandings. This Agreement may be executed in counterparts, each of which shall be deemed an original, but all of which together shall constitute one and the same instrument.")

    pdf.add_schedule_heading("ANNEXURE A: DETAILED JOB DESCRIPTION AND KRAs")
    pdf.add_clause_text("Role: Senior Software Engineer - AI/ML Platform")
    pdf.add_clause_text("Key Responsibilities:")
    pdf.add_clause_text("1. Architect and develop scalable backend microservices for the core AI platform.")
    pdf.add_clause_text("2. Optimize machine learning model deployment pipelines for low-latency inference.")
    pdf.add_clause_text("3. Mentor junior engineers and conduct rigorous code reviews.")
    pdf.add_clause_text("4. Collaborate cross-functionally with product and data science teams.")

    pdf.add_schedule_heading("ANNEXURE B: ESOP GRANT LETTER SUMMARY")
    pdf.add_clause_text("Grant Date: 15th October 2025")
    pdf.add_clause_text("Number of Options Granted: 800")
    pdf.add_clause_text("Exercise Price: Rs. 10 per share")
    pdf.add_clause_text("Vesting Schedule:")
    pdf.add_clause_text("- 15th October 2026: 200 Options (25% Cliff)")
    pdf.add_clause_text("- Subsequent Quarters: 50 Options per quarter for the next 12 quarters")

    pdf.add_schedule_heading("ANNEXURE C: LIST OF COMPANY POLICIES")
    pdf.add_clause_text("The Employee acknowledges the applicability of the following policies (subject to updates):")
    pdf.add_clause_text("1. Code of Business Conduct and Ethics (Effective: Jan 2024)")
    pdf.add_clause_text("2. Prevention of Sexual Harassment (POSH) Policy (Effective: Jan 2024)")
    pdf.add_clause_text("3. Information Security and Data Privacy Policy (Effective: March 2024)")
    pdf.add_clause_text("4. Travel and Expense Reimbursement Policy (Effective: June 2024)")

    parties = [
        {"role": "FOR NOVATECH SOLUTIONS PVT LTD", "name": "Authorized Signatory"},
        {"role": "EMPLOYEE", "name": "Amit Kumar Verma"}
    ]
    pdf.add_signature_block(parties)

    output_path = os.path.join(output_dir, "employment_agreement.pdf")
    pdf.output(output_path)
    return pdf.page_no()


if __name__ == "__main__":
    output_directory = r"C:\Users\pc\.gemini\antigravity\scratch\production-rag-pipeline\data\sample_pdfs"
    os.makedirs(output_directory, exist_ok=True)
    
    print(f"Generating documents in: {output_directory}")
    
    pages_doc1 = generate_residential_agreement(output_directory)
    print(f"Successfully generated Residential Rental Agreement ({pages_doc1} pages)")
    
    pages_doc2 = generate_employment_agreement(output_directory)
    print(f"Successfully generated Employment Agreement ({pages_doc2} pages)")
    
    print("All documents generated successfully.")
