import os
from fpdf import FPDF

class LegalPDF(FPDF):
    def header(self):
        self.set_font("Times", "B", 10)
        self.cell(0, 10, "LEGAL DOCUMENT", align="R")
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("Times", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def add_title(self, text):
        self.set_font("Times", "B", 16)
        self.multi_cell(0, 10, text, align="C")
        self.ln(5)
        
    def add_subtitle(self, text):
        self.set_font("Times", "B", 12)
        self.multi_cell(0, 8, text, align="C")
        self.ln(5)

    def add_preamble(self, text):
        self.set_font("Times", "", 11)
        self.multi_cell(0, 6, text, align="J")
        self.ln(5)

    def add_clause_heading(self, number, title):
        self.ln(5)
        self.set_font("Times", "B", 12)
        self.cell(0, 8, f"{number}. {title}", ln=True)

    def add_clause_text(self, text):
        self.set_font("Times", "", 11)
        self.multi_cell(0, 6, text, align="J")
        self.ln(2)

    def add_subclause(self, number, text):
        self.set_font("Times", "", 11)
        self.set_x(20)
        self.multi_cell(0, 6, f"{number} {text}", align="J")
        self.set_x(10)
        self.ln(2)

    def add_schedule_heading(self, title):
        self.add_page()
        self.set_font("Times", "B", 14)
        self.multi_cell(0, 10, title, align="C")
        self.ln(5)

    def add_signature_block(self, parties):
        self.ln(10)
        self.set_font("Times", "", 11)
        self.cell(0, 6, "IN WITNESS WHEREOF, the Parties hereto have executed this Agreement on the date first above written.", ln=True)
        self.ln(10)
        
        y = self.get_y()
        self.set_font("Times", "B", 11)
        self.cell(95, 6, f"For and on behalf of {parties[0]['name']}:", ln=False)
        self.cell(95, 6, f"For and on behalf of {parties[1]['name']}:", ln=True)
        
        self.ln(15)
        
        self.set_font("Times", "", 11)
        self.cell(95, 6, "_____________________________", ln=False)
        self.cell(95, 6, "_____________________________", ln=True)
        
        self.cell(95, 6, f"Name: {parties[0]['rep']}", ln=False)
        self.cell(95, 6, f"Name: {parties[1]['rep']}", ln=True)
        
        self.cell(95, 6, f"Title: {parties[0]['title']}", ln=False)
        self.cell(95, 6, f"Title: {parties[1]['title']}", ln=True)
        
        self.ln(10)
        
        self.set_font("Times", "B", 11)
        self.cell(95, 6, "Witness 1:", ln=False)
        self.cell(95, 6, "Witness 2:", ln=True)
        
        self.ln(10)
        
        self.set_font("Times", "", 11)
        self.cell(95, 6, "_____________________________", ln=False)
        self.cell(95, 6, "_____________________________", ln=True)
        
        self.cell(95, 6, "Name: _______________________", ln=False)
        self.cell(95, 6, "Name: _______________________", ln=True)

    def add_separator(self):
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

def generate_nda(output_dir):
    pdf = LegalPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.add_title("MUTUAL NON-DISCLOSURE AGREEMENT")
    
    pdf.add_preamble("This Mutual Non-Disclosure Agreement (the \"Agreement\") is entered into on this 1st day of September 2026 (the \"Effective Date\"), by and between:")
    
    pdf.add_preamble("NovaTech Solutions Private Limited, a company incorporated under the Companies Act, 2013, bearing CIN U72200KA2019PTC128456, having its registered office at 5th Floor, Tower B, Prestige Tech Park, Outer Ring Road, Marathahalli, Bangalore - 560037, represented by Mr. Karthik Subramanian, Chief Technology Officer (hereinafter referred to as the \"Disclosing Party\", which expression shall, unless repugnant to the context or meaning thereof, be deemed to mean and include its successors and permitted assigns);")
    
    pdf.add_preamble("AND")
    
    pdf.add_preamble("DataFlow Analytics LLP, a limited liability partnership incorporated under the Limited Liability Partnership Act, 2008, bearing LLPIN AAB-4521, having its registered office at 3rd Floor, Platina Tower, MG Road, Gurgaon, Haryana - 122002, represented by Ms. Ananya Desai, Managing Partner (hereinafter referred to as the \"Receiving Party\", which expression shall, unless repugnant to the context or meaning thereof, be deemed to mean and include its successors and permitted assigns).")
    
    pdf.add_preamble("The Disclosing Party and the Receiving Party are hereinafter individually referred to as a \"Party\" and collectively as the \"Parties\".")
    
    pdf.add_preamble("WHEREAS the Parties are exploring a potential technology partnership for the development and integration of an AI/ML-powered data pipeline orchestration platform (the \"Purpose\").")
    pdf.add_preamble("WHEREAS in connection with the Purpose, the Parties may disclose to each other certain confidential and proprietary information, and wish to set forth the terms and conditions governing the protection and use of such information.")
    
    pdf.add_clause_heading("1", "DEFINITIONS AND INTERPRETATION")
    pdf.add_clause_text("In this Agreement, the following terms shall have the meanings ascribed to them below unless the context otherwise requires:")
    pdf.add_subclause("1.1", "\"Affiliate\" means any entity that directly or indirectly Controls, is Controlled by, or is under common Control with a Party.")
    pdf.add_subclause("1.2", "\"Authorized Representatives\" means the directors, officers, employees, agents, and professional advisors of the Receiving Party who need to know the Confidential Information for the Permitted Purpose.")
    pdf.add_subclause("1.3", "\"Confidential Information\" means any and all information of a confidential, proprietary, or secret nature disclosed by the Disclosing Party to the Receiving Party, whether in written, oral, electronic, visual, or any other form. This includes, but is not limited to, technical, financial, business, customer, product, and strategic information, trade secrets, know-how, algorithms, source code, business plans, pricing, financial projections, employee information, vendor agreements, and ANY information that a reasonable person would consider confidential.")
    pdf.add_subclause("1.4", "\"Disclosing Party\" means the Party disclosing Confidential Information to the other Party.")
    pdf.add_subclause("1.5", "\"Effective Date\" means the date first written above.")
    pdf.add_subclause("1.6", "\"Permitted Purpose\" means the evaluation, discussion, and negotiation regarding the potential technology partnership for the development and integration of the AI/ML-powered data pipeline orchestration platform.")
    pdf.add_subclause("1.7", "\"Personnel\" means the employees, officers, directors, and independent contractors of a Party.")
    pdf.add_subclause("1.8", "\"Receiving Party\" means the Party receiving Confidential Information from the Disclosing Party.")
    pdf.add_subclause("1.9", "\"Representatives\" means the Affiliates, Personnel, and professional advisors of a Party.")
    pdf.add_subclause("1.10", "\"Residual Knowledge\" means information that is retained in the unaided memory of the Receiving Party's Personnel who have had access to the Confidential Information.")
    pdf.add_subclause("1.11", "\"Territory\" means the Republic of India and any other jurisdiction worldwide where the Parties operate.")
    pdf.add_subclause("1.12", "\"Work Product\" means any notes, analyses, compilations, studies, interpretations, memoranda, or other documents prepared by the Receiving Party that contain, reflect, or are based upon, in whole or in part, the Confidential Information.")

    pdf.add_clause_heading("2", "SCOPE OF CONFIDENTIAL INFORMATION")
    pdf.add_clause_text("The term Confidential Information includes all information disclosed in written, oral, visual, electronic, or any other form. It expressly includes any information disclosed by the Disclosing Party prior to the execution of this Agreement if such information is related to the Purpose. Furthermore, all Work Product, notes, analyses, compilations, studies, interpretations, and memoranda prepared by the Receiving Party that contain, reflect, or are derived from the Confidential Information shall be treated as Confidential Information. While marking information as 'Confidential' or 'Proprietary' is preferred, it is not required for information that is reasonably understood to be confidential by its nature or the context of its disclosure.")

    pdf.add_clause_heading("3", "OBLIGATIONS OF RECEIVING PARTY")
    pdf.add_clause_text("The Receiving Party shall protect the Confidential Information with the same degree of care it uses to protect its own confidential information of a similar nature, but in no event less than a reasonable degree of care. The Receiving Party shall restrict access to the Confidential Information solely to its Representatives who have a strict 'need-to-know' for the Permitted Purpose and who are bound by written confidentiality obligations no less restrictive than those contained herein. The Receiving Party shall not copy or reproduce the Confidential Information except as strictly necessary for the Permitted Purpose. The Receiving Party agrees not to reverse engineer, decompile, disassemble, or derive the source code of any software or physical objects containing Confidential Information. The Receiving Party shall promptly notify the Disclosing Party in writing of any unauthorized disclosure or use of the Confidential Information and shall be fully responsible for any breach of this Agreement by its Representatives.")

    pdf.add_clause_heading("4", "EXCLUSIONS FROM CONFIDENTIAL INFORMATION")
    pdf.add_clause_text("The obligations of confidentiality under this Agreement shall not apply to information that the Receiving Party can establish by documentary evidence: (a) was already lawfully known to the Receiving Party prior to its disclosure by the Disclosing Party; (b) was independently developed by the Receiving Party without access to or reference to the Confidential Information; (c) was received from a third party without any restriction on disclosure and without breach of any obligation of confidentiality; or (d) is or becomes publicly available through no act or omission of the Receiving Party. If the Receiving Party is required to disclose Confidential Information by law, regulation, or a valid court order, such disclosure shall not constitute a breach, provided the Receiving Party gives prompt advance written notice to the Disclosing Party and reasonably cooperates to seek a protective order or otherwise limit the scope of the required disclosure.")

    pdf.add_clause_heading("5", "PERMITTED DISCLOSURES")
    pdf.add_clause_text("The Receiving Party is permitted to disclose Confidential Information only: (a) to its Authorized Representatives who require access strictly for the Permitted Purpose; (b) to its professional advisors (such as lawyers and accountants) who are under a professional duty of confidentiality; and (c) as required by applicable law, statutory regulation, or legal process, provided that the Receiving Party gives prompt written notice to the Disclosing Party (to the extent legally permissible) and reasonably cooperates with the Disclosing Party's efforts to limit the scope of the disclosure or obtain a protective order. Disclosures to regulatory authorities as strictly required by law are also permitted under the same conditions of prior notice and cooperation.")

    pdf.add_clause_heading("6", "TERM AND SURVIVAL")
    pdf.add_clause_text("This Agreement shall become effective on the Effective Date and shall remain in full force and effect for a period of three (3) years, unless terminated earlier by mutual written agreement of the Parties. The confidentiality obligations set forth herein shall survive the expiration or termination of this Agreement for a period of five (5) years from the date of disclosure of each specific piece of Confidential Information. Notwithstanding the foregoing, any Confidential Information that constitutes a trade secret under applicable law shall remain protected for as long as such information continues to qualify as a trade secret.")

    pdf.add_clause_heading("7", "RETURN AND DESTRUCTION OF INFORMATION")
    pdf.add_clause_text("Within fifteen (15) business days following a written request from the Disclosing Party, or immediately upon the termination or expiration of this Agreement, the Receiving Party shall, at the Disclosing Party's option, either return or destroy all Confidential Information, including all copies, notes, analyses, and Work Product. Any electronic copies shall be permanently deleted, and the Receiving Party shall provide a written certification of destruction signed by an authorized officer. The Receiving Party may retain one (1) archival copy of the Confidential Information solely for legal, regulatory, or compliance purposes, provided such copy remains subject to the confidentiality obligations herein. Furthermore, Confidential Information residing in routine automated electronic backup systems is exempt from immediate destruction, provided that such backup systems are not accessed or restored for any business purpose.")

    pdf.add_clause_heading("8", "INTELLECTUAL PROPERTY AND OWNERSHIP")
    pdf.add_clause_text("All Confidential Information shall remain the exclusive property of the Disclosing Party. Nothing in this Agreement shall be construed as granting, either expressly or by implication, estoppel, or otherwise, any license, right, title, or interest in or to any patent, trademark, copyright, trade secret, or other intellectual property right of the Disclosing Party, except the limited right to use the Confidential Information solely for the Permitted Purpose. The Receiving Party shall not reverse engineer any hardware or software containing the Confidential Information. The Parties agree that all analyses, compilations, and other Work Product prepared by the Receiving Party that contain or reflect the Confidential Information shall be deemed the Confidential Information of the Disclosing Party and subject to the terms of this Agreement.")

    pdf.add_clause_heading("9", "NO REPRESENTATIONS OR WARRANTIES")
    pdf.add_clause_text("All Confidential Information is provided 'AS-IS' and without any warranty whatsoever. The Disclosing Party makes no representations or warranties, express or implied, regarding the accuracy, completeness, or fitness for a particular purpose of the Confidential Information. The Receiving Party acknowledges that it relies on the Confidential Information at its own risk. Nothing in this Agreement shall impose any obligation on the Disclosing Party to disclose any particular information or to proceed with any transaction or relationship. The Disclosing Party makes no warranty that the use of the Confidential Information will not infringe the intellectual property rights of any third party.")

    pdf.add_clause_heading("10", "REMEDIES")
    pdf.add_clause_text("The Receiving Party acknowledges that a breach of its obligations under this Agreement may cause irreparable harm to the Disclosing Party for which monetary damages would be inadequate. Accordingly, the Disclosing Party shall be entitled to seek injunctive relief, specific performance, and other equitable remedies to prevent or restrain a breach, without the necessity of proving actual damages or posting a bond. The Receiving Party shall indemnify, defend, and hold harmless the Disclosing Party from and against all losses, damages, costs, and expenses (including reasonable attorneys' fees) arising directly from any breach of this Agreement by the Receiving Party or its Representatives. These indemnification obligations shall survive the termination or expiration of this Agreement.")

    pdf.add_clause_heading("11", "NO OBLIGATION TO TRANSACT")
    pdf.add_clause_text("This Agreement does not obligate either Party to enter into any business relationship, joint venture, transaction, or further agreement with the other Party. Either Party may terminate discussions regarding the Permitted Purpose at any time, for any reason or no reason, without any liability to the other Party, subject only to the surviving confidentiality obligations set forth herein.")

    pdf.add_clause_heading("12", "NON-SOLICITATION")
    pdf.add_clause_text("During the term of this Agreement and for a period of twelve (12) months thereafter, neither Party shall, directly or indirectly, solicit for employment, hire, or engage any employee or contractor of the other Party with whom it had material contact in connection with the Permitted Purpose. However, this restriction shall not apply to general recruitment advertising not specifically targeted at the other Party's employees, or the hiring of individuals who independently approach a Party for employment without any prior solicitation.")

    pdf.add_clause_heading("13", "PUBLICITY")
    pdf.add_clause_text("Neither Party shall make any public announcement, press release, or other public disclosure regarding the existence of this Agreement, the nature of the discussions between the Parties, or the content of the Confidential Information without the prior written consent of the other Party, except as strictly required by applicable law or stock exchange regulations.")

    pdf.add_clause_heading("14", "GOVERNING LAW")
    pdf.add_clause_text("This Agreement and all matters arising out of or relating to it shall be governed by, construed, and interpreted in accordance with the laws of the Republic of India, without regard to its conflict of law principles.")

    pdf.add_clause_heading("15", "DISPUTE RESOLUTION")
    pdf.add_clause_text("Any dispute, controversy, or claim arising out of or relating to this Agreement, or the breach, termination, or invalidity thereof, shall first be subject to good faith negotiation between senior executives of the Parties for a period of thirty (30) days. If the dispute remains unresolved, it shall be finally settled by arbitration in accordance with the Rules of Arbitration of the International Chamber of Commerce (ICC Rules). The arbitral tribunal shall consist of a sole arbitrator appointed in accordance with the ICC Rules. The seat and venue of the arbitration shall be New Delhi, India, and the language of the arbitration shall be English. The arbitral award shall be final and binding. Each Party shall bear its own costs, except that the prevailing Party shall be entitled to recover its reasonable attorneys' fees and arbitration costs.")

    pdf.add_clause_heading("16", "ASSIGNMENT")
    pdf.add_clause_text("Neither Party may assign or transfer this Agreement or any of its rights or obligations hereunder without the prior written consent of the other Party. Notwithstanding the foregoing, either Party may assign this Agreement to an Affiliate or in connection with a merger, acquisition, corporate reorganization, or sale of all or substantially all of its assets, provided that the assignee assumes all obligations under this Agreement in writing. Any attempted assignment in violation of this clause shall be null and void.")

    pdf.add_clause_heading("17", "AMENDMENT AND WAIVER")
    pdf.add_clause_text("This Agreement may only be amended, modified, or supplemented by a written instrument signed by the authorized representatives of both Parties. No failure or delay by either Party in exercising any right, power, or privilege hereunder shall operate as a waiver thereof, nor shall any single or partial exercise thereof preclude any other or further exercise thereof or the exercise of any other right, power, or privilege. A waiver of any breach shall not be deemed a waiver of any subsequent breach.")

    pdf.add_clause_heading("18", "SEVERABILITY")
    pdf.add_clause_text("If any provision of this Agreement is held to be invalid, illegal, or unenforceable by a court of competent jurisdiction, the remaining provisions of this Agreement shall continue in full force and effect. The Parties agree to negotiate in good faith to modify the invalid provision to the minimum extent necessary to make it valid and enforceable while preserving the original intent of the Parties.")

    pdf.add_clause_heading("19", "NOTICES")
    pdf.add_clause_text("All notices, requests, demands, and other communications required or permitted under this Agreement shall be in writing and shall be deemed duly given: (a) upon personal delivery on the same day; (b) three (3) business days after being sent by recognized national courier; or (c) upon receipt of delivery confirmation when sent by email. Notices shall be addressed to the respective Parties at the addresses set forth in the preamble of this Agreement or to such other addresses as a Party may designate by written notice.")

    pdf.add_clause_heading("20", "ENTIRE AGREEMENT AND COUNTERPARTS")
    pdf.add_clause_text("This Agreement constitutes the entire agreement between the Parties with respect to the subject matter hereof and supersedes all prior or contemporaneous oral or written agreements, understandings, or representations relating thereto. This Agreement may be executed in one or more counterparts, each of which shall be deemed an original, but all of which together shall constitute one and the same instrument. Electronic or digital signatures shall have the same legal effect as original wet-ink signatures.")

    parties = [
        {"name": "NovaTech Solutions Private Limited", "rep": "Karthik Subramanian", "title": "Chief Technology Officer"},
        {"name": "DataFlow Analytics LLP", "rep": "Ananya Desai", "title": "Managing Partner"}
    ]
    pdf.add_signature_block(parties)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "mutual_nda_agreement.pdf")
    pdf.output(out_path)
    print(f"Generated {out_path} ({pdf.page_no()} pages)")

def generate_freelance(output_dir):
    pdf = LegalPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.add_title("FREELANCE SERVICE AGREEMENT")
    
    pdf.add_preamble("This Freelance Service Agreement (the \"Agreement\") is entered into on this 10th day of September 2026 (the \"Effective Date\"), by and between:")
    
    pdf.add_preamble("CreativeMinds Digital Private Limited, a company incorporated under the Companies Act, 2013, bearing CIN U74999MH2020PTC345678, having its registered office at 12th Floor, One BKC, Bandra Kurla Complex, Mumbai - 400051, represented by Ms. Ritu Kapoor, Head of Product Design (hereinafter referred to as the \"Company\", which expression shall, unless repugnant to the context or meaning thereof, be deemed to mean and include its successors and permitted assigns);")
    
    pdf.add_preamble("AND")
    
    pdf.add_preamble("Ms. Sneha Reddy, D/o Shri Venkateshwar Reddy, an independent consultant having PAN KLMPR7890E and GST Registration Number 36KLMPR7890E1ZA, residing at Flat 201, Prestige Orchid Apartments, Road No. 12, Jubilee Hills, Hyderabad, Telangana - 500033 (hereinafter referred to as the \"Freelancer\", which expression shall, unless repugnant to the context or meaning thereof, be deemed to mean and include her heirs, executors, administrators, and assigns).")
    
    pdf.add_preamble("The Company and the Freelancer are hereinafter individually referred to as a \"Party\" and collectively as the \"Parties\".")
    
    pdf.add_preamble("WHEREAS the Company desires to engage the Freelancer to provide UI/UX Design services for a mobile application project, and the Freelancer agrees to provide such services subject to the terms and conditions set forth herein.")
    pdf.add_preamble("PROJECT: UI/UX Design for Mobile Application \"HealthTrack Pro\" - a health and wellness tracking application for iOS and Android platforms.")
    
    pdf.add_clause_heading("1", "DEFINITIONS")
    pdf.add_clause_text("In this Agreement, the following terms shall have the specified meanings:")
    pdf.add_subclause("1.1", "\"Acceptance\" means the formal written approval by the Company of any Deliverable, signifying that it meets the Specifications.")
    pdf.add_subclause("1.2", "\"Company Materials\" means all materials, data, brand guidelines, and assets provided by the Company to the Freelancer.")
    pdf.add_subclause("1.3", "\"Confidential Information\" means all non-public information related to the Company's business, the Project, and users.")
    pdf.add_subclause("1.4", "\"Deliverables\" means the specific output and materials to be provided by the Freelancer as outlined in Clause 3.")
    pdf.add_subclause("1.5", "\"Effective Date\" means the date first written above.")
    pdf.add_subclause("1.6", "\"Feedback\" means any comments, suggestions, or change requests provided by the Company.")
    pdf.add_subclause("1.7", "\"Final Delivery Date\" means the agreed deadline for the submission of all final Deliverables.")
    pdf.add_subclause("1.8", "\"Intellectual Property Rights\" means all patents, copyrights, trademarks, design rights, and other intellectual property.")
    pdf.add_subclause("1.9", "\"Milestone\" means a specific phase of the Project linked to deliverables and payment.")
    pdf.add_subclause("1.10", "\"Project\" means the UI/UX Design for the HealthTrack Pro mobile application.")
    pdf.add_subclause("1.11", "\"Revision\" means a set of changes to existing deliverables within the original scope.")
    pdf.add_subclause("1.12", "\"Services\" means the design and related services provided by the Freelancer under this Agreement.")
    pdf.add_subclause("1.13", "\"Specifications\" means the technical and design requirements for the Project.")
    pdf.add_subclause("1.14", "\"Work Product\" means all drafts, materials, and concepts created during the provision of Services.")

    pdf.add_clause_heading("2", "SCOPE OF SERVICES")
    pdf.add_clause_text("The Freelancer shall provide the following Services, structured into phases:")
    pdf.add_subclause("2.1", "Phase 1 - Discovery and Research (Weeks 1-2): Conduct user research interviews with a minimum of 10 participants, perform competitive analysis on 5 competitor applications, develop 3 detailed user personas, construct comprehensive user journey maps, and create information architecture documentation.")
    pdf.add_subclause("2.2", "Phase 2 - Wireframing (Weeks 3-4): Create low-fidelity wireframes for all application screens (minimum of 25 screens), develop detailed user flow diagrams, establish the navigation structure, and participate in wireframe review and iterative refinement.")
    pdf.add_subclause("2.3", "Phase 3 - High-Fidelity Design (Weeks 5-7): Present visual design explorations featuring 3 distinct design directions. Upon selection by the Company, refine the chosen direction and produce high-fidelity mockups for all screens with both iOS and Android variants, accompanied by interaction specifications and micro-animation storyboards.")
    pdf.add_subclause("2.4", "Phase 4 - Design System and Handoff (Weeks 8-9): Deliver a comprehensive component library in Figma comprising a minimum of 50 components. This must include a typography scale, color system, spacing system, a custom icon set of at least 40 icons, detailed design tokens documentation, and complete developer handoff documentation integrated with Zeplin.")

    pdf.add_clause_heading("3", "DELIVERABLES")
    pdf.add_clause_text("The Freelancer agrees to provide the following specific Deliverables:")
    pdf.add_clause_text("For Phase 1: Research report PDF, persona documents. For Phase 2: Complete wireframe files and user flow diagrams. For Phase 3: Final high-fidelity mockup files in Figma for iOS and Android. For Phase 4: A centralized design system file, complete icon library, fully configured Zeplin project for developer handoff, and a comprehensive design specification document. All digital files must be fully editable and organized systematically.")

    pdf.add_clause_heading("4", "TIMELINE AND MILESTONES")
    pdf.add_clause_text("The Services shall be completed in accordance with the timeline specified in Schedule B. Each milestone includes a review period of five (5) business days for the Company to provide Feedback. Any delay resulting from the Company's late provision of Feedback, materials, or necessary approvals shall automatically extend the corresponding deadline and the Final Delivery Date proportionally.")

    pdf.add_clause_heading("5", "COMPENSATION")
    pdf.add_subclause("5.1", "Total Project Fee: Rs. 5,50,000 (exclusive of applicable GST).")
    pdf.add_subclause("5.2", "GST: Goods and Services Tax at 18% shall be applicable, amounting to Rs. 99,000.")
    pdf.add_subclause("5.3", "Payment Schedule: The fees shall be payable as follows: 15% advance upon signing (Rs. 82,500 + GST); 25% upon completion and Acceptance of Phase 1 (Rs. 1,37,500 + GST); 25% upon completion and Acceptance of Phase 2 (Rs. 1,37,500 + GST); 25% upon completion and Acceptance of Phase 3 (Rs. 1,37,500 + GST); and the final 10% upon final delivery and Acceptance of all Project Deliverables (Rs. 55,000 + GST).")
    pdf.add_subclause("5.4", "Payment Terms: The Freelancer shall raise a formal invoice upon the completion of each milestone. The Company shall process and release the payment within fifteen (15) business days of invoice approval. Any late payment shall attract interest at the rate of 1.5% per month until fully paid.")
    pdf.add_subclause("5.5", "Expenses: All pre-approved out-of-pocket expenses, including travel, user research participant incentives, and premium stock assets, shall be reimbursed by the Company at actuals, subject to the submission of valid receipts.")

    pdf.add_clause_heading("6", "REVISIONS AND CHANGES")
    pdf.add_subclause("6.1", "Included Revisions: The agreed fee includes up to two (2) rounds of revisions per phase at no additional cost.")
    pdf.add_subclause("6.2", "Additional Revisions: Any further rounds of revision requested by the Company shall be billed at Rs. 18,000 per additional revision round.")
    pdf.add_subclause("6.3", "Scope Changes: Any material changes to the scope of the Project must be documented in a written Change Order (as per Schedule C) signed by both Parties, which shall specify any adjusted timelines and additional compensation.")
    pdf.add_subclause("6.4", "Definition of Revision: A revision is defined strictly as a set of modifications to existing deliverables. A request for entirely new deliverables or features not included in the original Scope of Services constitutes a Scope Change, not a Revision.")

    pdf.add_clause_heading("7", "INTELLECTUAL PROPERTY")
    pdf.add_subclause("7.1", "Work Product Assignment: Upon receipt of full and final payment, all Intellectual Property Rights in the Deliverables and Work Product shall be assigned to the Company absolutely and irrevocably, worldwide and in perpetuity.")
    pdf.add_subclause("7.2", "Pre-Assignment Rights: Until full payment is received by the Freelancer, all Intellectual Property Rights remain with the Freelancer. The Company may not use, publish, or implement any Deliverables for which payment is outstanding.")
    pdf.add_subclause("7.3", "Pre-Existing IP: The Freelancer's pre-existing tools, templates, frameworks, and methodologies remain the sole property of the Freelancer. The Company receives a non-exclusive, perpetual, royalty-free license to use any such pre-existing IP strictly as incorporated into the final Deliverables.")
    pdf.add_subclause("7.4", "Portfolio Rights: The Freelancer retains the right to showcase the completed work in their personal portfolio, website, and award submissions after the public launch of the application, subject to the Company's prior written consent, which shall not be unreasonably withheld.")
    pdf.add_subclause("7.5", "Rejected Work: All concepts, sketches, and preliminary designs not included in the final Deliverables remain the property of the Company if they were developed using the Company's Confidential Information or Specifications.")

    pdf.add_clause_heading("8", "TOOLS AND RESOURCES")
    pdf.add_clause_text("The Company shall provide the Freelancer with access to a Figma Business license and Zeplin enterprise access for the duration of the Project. The Freelancer is responsible for providing their own hardware, internet connection, and any other additional software required to perform the Services. The Company shall supply all necessary brand guidelines, existing digital assets, and facilitate access to key stakeholders for interviews and feedback.")

    pdf.add_clause_heading("9", "COMMUNICATION AND REPORTING")
    pdf.add_clause_text("The Freelancer shall provide weekly progress reports via email every Friday. The Parties shall conduct bi-weekly video sync calls to review progress and address blockers. Day-to-day communication shall occur via a dedicated Slack channel provided by the Company. The Freelancer commits to a 24-hour response time during standard business hours. All work files and assets must be actively maintained and updated in the Company's designated Figma workspace.")

    pdf.add_clause_heading("10", "CONFIDENTIALITY")
    pdf.add_clause_text("The Freelancer acknowledges that product features, business strategies, user data, and unreleased product information constitute Confidential Information of the Company. The Freelancer agrees not to disclose such information to any third party and to use it solely for the performance of the Services. These confidentiality obligations shall survive for a period of twenty-four (24) months post-termination of this Agreement. The only exception to this obligation is the permitted portfolio use as explicitly outlined in Clause 7.4.")

    pdf.add_clause_heading("11", "INDEPENDENT CONTRACTOR STATUS")
    pdf.add_clause_text("The relationship of the Freelancer to the Company is that of an independent contractor, and not that of an employee, agent, or partner. The Freelancer shall not be entitled to any employment benefits, workers' compensation, or paid leave. The Freelancer is solely responsible for reporting and paying their own taxes, including income tax and applicable GST. The Freelancer may engage subcontractors only with the prior written and express consent of the Company.")

    pdf.add_clause_heading("12", "REPRESENTATIONS AND WARRANTIES")
    pdf.add_clause_text("The Freelancer represents and warrants that all work provided will be original, will not infringe upon the intellectual property or third-party rights of any entity, that they have full right and authority to enter into this Agreement, and that they have no conflicting obligations. The Company represents and warrants that it has the authority to enter into this Agreement, will provide timely and constructive feedback, and holds all necessary rights and licenses to the materials and assets it provides to the Freelancer.")

    pdf.add_clause_heading("13", "LIMITATION OF LIABILITY")
    pdf.add_clause_text("The Freelancer's total aggregate liability arising out of or in connection with this Agreement shall be strictly capped at the total amount of fees actually received under this Agreement. Under no circumstances shall either Party be liable for any indirect, consequential, incidental, special, or punitive damages, or loss of profits. The Company's liability for its payment obligations is unlimited. However, the Freelancer remains fully liable without a cap for any third-party claims arising out of intellectual property infringement caused by the Freelancer's original work.")

    pdf.add_clause_heading("14", "TERMINATION")
    pdf.add_subclause("14.1", "By Company for Convenience: The Company may terminate this Agreement at any time by providing fifteen (15) business days written notice, subject to full payment for all work completed and accepted, plus a pro-rated payment for any work currently in progress.")
    pdf.add_subclause("14.2", "By Freelancer for Convenience: The Freelancer may terminate this Agreement by providing thirty (30) calendar days written notice, ensuring the completion of the current phase or a satisfactory handover of all materials, and the prompt refund of any advance payments received for undelivered work.")
    pdf.add_subclause("14.3", "For Cause: Either Party may terminate this Agreement for a material breach that remains uncured after a seven (7) business days cure period following written notice. Termination shall be immediate if the breach is incapable of cure. Material breach includes missing deadlines by more than 10 business days, delivering work consistently below professional standards, or breach of confidentiality.")
    pdf.add_subclause("14.4", "Effect: Upon termination, the Company shall receive all completed Deliverables and in-progress Work Product corresponding to the payments made. The Freelancer must return or destroy all Company Materials. The clauses relating to Intellectual Property, Confidentiality, and Limitation of Liability shall survive termination.")

    pdf.add_clause_heading("15", "NON-SOLICITATION")
    pdf.add_clause_text("During the term of this Agreement and for twelve (12) months thereafter, the Freelancer shall not directly or indirectly solicit, recruit, or hire any employee or contractor of the Company. Furthermore, the Freelancer shall not directly approach, solicit, or engage any of the Company's clients whose confidential information the Freelancer accessed during the execution of the Project.")

    pdf.add_clause_heading("16", "DISPUTE RESOLUTION")
    pdf.add_clause_text("Any dispute arising out of this Agreement shall first be subject to good faith negotiation between the Parties for fifteen (15) days. If unresolved, the dispute shall proceed to mediation for thirty (30) days. Any dispute remaining unresolved shall be finally settled by arbitration administered by the Mumbai Centre for International Arbitration (MCIA) in accordance with MCIA Rules. The tribunal shall consist of a sole arbitrator, and the language of the arbitration shall be English. The seat of arbitration shall be Mumbai.")

    pdf.add_clause_heading("17", "GOVERNING LAW")
    pdf.add_clause_text("This Agreement shall be governed by and construed in accordance with the laws of the Republic of India. Subject to the dispute resolution clause, the courts at Mumbai shall have exclusive jurisdiction over any matters arising from this Agreement.")

    pdf.add_clause_heading("18", "FORCE MAJEURE")
    pdf.add_clause_text("Neither Party shall be liable for any delay or failure to perform its obligations under this Agreement if such delay or failure is caused by events beyond their reasonable control, including but not limited to acts of God, pandemics, government restrictions, or severe internet or infrastructure failures, provided the affected Party promptly notifies the other Party.")

    pdf.add_clause_heading("19", "SEVERABILITY, NOTICES, ENTIRE AGREEMENT, COUNTERPARTS")
    pdf.add_clause_text("If any provision is held invalid, the remainder shall continue in effect. Notices shall be in writing by email or registered post. This document constitutes the entire agreement and supersedes all prior communications. It may be executed in counterparts.")

    pdf.add_schedule_heading("SCHEDULE A: Detailed Scope of Work with screen list")
    pdf.add_clause_text("Detailed listing of all 25+ application screens, user flows, and specific design system requirements as agreed between the Parties.")
    
    pdf.add_schedule_heading("SCHEDULE B: Milestone Dates")
    pdf.add_clause_text("Phase 1 Completion: Week 2\nPhase 2 Completion: Week 4\nPhase 3 Completion: Week 7\nPhase 4 Completion: Week 9")
    
    pdf.add_schedule_heading("SCHEDULE C: Change Order Template")
    pdf.add_clause_text("Standard template for recording any deviations in scope, revised timelines, and additional costs.")

    parties = [
        {"name": "CreativeMinds Digital Private Limited", "rep": "Ritu Kapoor", "title": "Head of Product Design"},
        {"name": "Ms. Sneha Reddy", "rep": "Sneha Reddy", "title": "Freelance UI/UX Designer"}
    ]
    pdf.add_signature_block(parties)

    out_path = os.path.join(output_dir, "freelance_service_agreement.pdf")
    pdf.output(out_path)
    print(f"Generated {out_path} ({pdf.page_no()} pages)")

def generate_lease(output_dir):
    pdf = LegalPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.add_title("COMMERCIAL LEASE AGREEMENT")
    
    pdf.add_preamble("This Commercial Lease Agreement (the \"Agreement\") is made and executed on this 1st day of November 2025 (the \"Execution Date\"), by and between:")
    
    pdf.add_preamble("Horizon Properties LLP, a limited liability partnership bearing LLPIN AAC-5678, represented by its Partners Mr. Suresh Reddy and Mrs. Lakshmi Reddy, having its registered office at Office No. 601, Mantri Square Mall, Sampige Road, Malleshwaram, Bangalore - 560003 (hereinafter referred to as the \"Lessor\", which expression shall, unless repugnant to the context or meaning thereof, be deemed to mean and include its successors and assigns);")
    
    pdf.add_preamble("AND")
    
    pdf.add_preamble("FreshBite Foods Private Limited, a company incorporated under the Companies Act, 2013, bearing CIN U55101KA2021PTC456789, having its registered office at No. 78, 100 Feet Road, Indiranagar, Bangalore - 560038, represented by Mr. Vikram Singh, Director (hereinafter referred to as the \"Lessee\", which expression shall, unless repugnant to the context or meaning thereof, be deemed to mean and include its successors and permitted assigns).")
    
    pdf.add_preamble("PROPERTY DESCRIPTION: Ground Floor Commercial Unit No. GF-04, \"Horizon Business Centre\", Plot No. 45/1, 14th Cross Road, HSR Layout Sector 2, Bangalore - 560102. The unit comprises a built-up area of 2,400 sq ft and a carpet area of 1,800 sq ft, including an attached kitchen area, storage room, and dedicated customer seating area.")
    
    pdf.add_clause_heading("1", "DEFINITIONS")
    pdf.add_clause_text("In this Agreement, the following terms shall have the meanings specified:")
    pdf.add_subclause("1.1", "\"Built-up Area\" means the total area of the Premises including the thickness of external walls and proportionate share of common areas.")
    pdf.add_subclause("1.2", "\"CAM Charges\" means the Common Area Maintenance charges levied for the upkeep of the building.")
    pdf.add_subclause("1.3", "\"Carpet Area\" means the net usable floor area of the Premises, excluding external walls, balcony, and terrace.")
    pdf.add_subclause("1.4", "\"Commencement Date\" means January 1, 2026, the date from which the Lease Term and rent obligations begin.")
    pdf.add_subclause("1.5", "\"Common Areas\" means staircases, elevators, lobbies, parking, and pathways available for joint use.")
    pdf.add_subclause("1.6", "\"Fitout Period\" means the rent-free period granted to the Lessee to carry out interior works.")
    pdf.add_subclause("1.7", "\"Landlord's Fixtures\" means structural components, standard electrical systems, and plumbing installed by the Lessor.")
    pdf.add_subclause("1.8", "\"Lease Term\" means the initial term of five years from the Commencement Date.")
    pdf.add_subclause("1.9", "\"Lessee's Fixtures\" means the trade fixtures, kitchen equipment, and decor installed by the Lessee.")
    pdf.add_subclause("1.10", "\"Lock-in Period\" means the initial three-year period during which neither party can terminate the lease without penalty.")
    pdf.add_subclause("1.11", "\"Maintenance\" means routine upkeep and repair works.")
    pdf.add_subclause("1.12", "\"Permitted Use\" means operating a restaurant, cafe, cloud kitchen, or food service business.")
    pdf.add_subclause("1.13", "\"Premises\" means the Ground Floor Commercial Unit No. GF-04 described above.")
    pdf.add_subclause("1.14", "\"Property Tax\" means municipal taxes levied on the building by local authorities.")
    pdf.add_subclause("1.15", "\"Rent\" means the monthly base rent payable by the Lessee to the Lessor.")
    pdf.add_subclause("1.16", "\"Rent Escalation\" means the annual percentage increase in the Rent.")
    pdf.add_subclause("1.17", "\"Rent-Free Period\" means the period prior to the Commencement Date where no Rent is payable.")
    pdf.add_subclause("1.18", "\"Security Deposit\" means the interest-free refundable deposit paid by the Lessee.")
    pdf.add_subclause("1.19", "\"Structure\" means the foundation, roof, load-bearing walls, and exterior facade.")
    pdf.add_subclause("1.20", "\"Trade Fixtures\" means equipment specific to the Lessee's business operations.")
    pdf.add_subclause("1.21", "\"Utilities\" means electricity, water, internet, and gas services.")

    pdf.add_clause_heading("2", "GRANT OF LEASE")
    pdf.add_clause_text("The Lessor hereby grants and demises unto the Lessee, and the Lessee accepts, the lease of the Premises along with the right to use the Premises solely for the Permitted Use. The Lessee is further granted the non-exclusive right to use the Common Areas in conjunction with other tenants of the building. The Lessor shall hand over possession of the Premises to the Lessee 15 days prior to the Commencement Date, providing a rent-free Fitout Period to facilitate the Lessee's interior works.")

    pdf.add_clause_heading("3", "LEASE TERM")
    pdf.add_clause_text("The initial Lease Term shall be for a period of five (5) years, commencing on the Commencement Date of 1st January 2026. The lease is subject to a strict lock-in period of three (3) years from the Commencement Date, binding upon both the Lessor and the Lessee. The Lessee shall have the option to renew the lease for one additional term of five (5) years on mutually agreed terms, provided the Lessee gives written notice of its intent to renew at least six (6) months prior to the expiration of the initial term. Any holding over by the Lessee post the expiration or termination of the lease without a registered renewal agreement shall be construed as a month-to-month tenancy, and the Lessee shall be liable to pay rent at 150% of the last applicable Rent.")

    pdf.add_clause_heading("4", "RENT AND ESCALATION")
    pdf.add_subclause("4.1", "Base Rent: The monthly Rent is fixed at Rs. 1,35,000 (calculated at Rs. 75 per sq ft on the carpet area of 1,800 sq ft).")
    pdf.add_subclause("4.2", "Rent Escalation: The Base Rent shall be subject to an escalation of 8% per annum, effective on each anniversary of the Commencement Date.")
    pdf.add_subclause("4.3", "CAM Charges: The Lessee shall pay monthly CAM Charges at Rs. 28 per sq ft on the built-up area, amounting to Rs. 67,200 per month, subject to annual revision based on actual building maintenance costs.")
    pdf.add_subclause("4.4", "Property Tax: The burden of municipal Property Tax shall be shared equally between the Lessor and the Lessee. The current estimated total property tax is approximately Rs. 1,80,000 per annum.")
    pdf.add_subclause("4.5", "GST: Goods and Services Tax, as applicable, shall be payable by the Lessee on both the Rent and CAM Charges over and above the stated amounts.")
    pdf.add_subclause("4.6", "Payment: Rent and CAM charges are due on or before the 1st day of each calendar month, payable via bank transfer, NEFT, or RTGS. Late payments shall attract interest at 18% per annum.")
    pdf.add_subclause("4.7", "TDS: The Lessee shall be responsible for deducting Tax Deducted at Source (TDS) as per applicable tax laws and shall provide valid TDS certificates to the Lessor on a quarterly basis.")

    pdf.add_clause_heading("5", "SECURITY DEPOSIT")
    pdf.add_clause_text("The Lessee has paid an interest-free, refundable Security Deposit of Rs. 8,10,000, equivalent to six (6) months' Rent at the initial rate. The Security Deposit shall be refunded to the Lessee within ninety (90) days of vacating the Premises, subject to deductions for any unpaid rent, charges, or damages beyond normal wear and tear. The Lessee is required to top up the Security Deposit proportionally upon each annual Rent escalation, remitting the difference within thirty (30) days of the effective date of such escalation.")

    pdf.add_clause_heading("6", "PERMITTED USE")
    pdf.add_clause_text("The Premises shall be strictly used as a restaurant, cafe, cloud kitchen, and general food service business. The Lessee guarantees that all food preparation and service operations will comply entirely with FSSAI regulations and local health codes. The Lessee shall not engage in any activity that creates a nuisance, excessive noise, or offensive odors affecting other tenants in the Horizon Business Centre. The sale of alcoholic beverages is strictly prohibited without the explicit prior written consent of the Lessor and the procurement of all applicable state excise licenses. Furthermore, the Lessee shall not host live music or entertainment events without obtaining prior written consent from the Lessor.")

    pdf.add_clause_heading("7", "FITOUT AND ALTERATIONS")
    pdf.add_subclause("7.1", "Fitout Period: A rent-free period of 15 days from the handover of possession is granted for fitout works.")
    pdf.add_subclause("7.2", "Lessee's Fitout: All interior fitout works, including but not limited to kitchen equipment, furniture, decor, internal signage, false ceiling, and specialized flooring, shall be executed at the Lessee's sole cost and risk.")
    pdf.add_subclause("7.3", "Structural Modifications: The Lessee is strictly prohibited from making any structural modifications to the Premises without the prior written consent of the Lessor. Any approved structural changes must be borne by the Lessee and certified by a licensed structural engineer.")
    pdf.add_subclause("7.4", "Removal of Fixtures: Upon the expiration or earlier termination of the Lease, the Lessee may remove its Trade Fixtures, provided that the Premises is restored to its original condition. Any fixtures not removed within 15 days of the lease end date shall automatically become the property of the Lessor.")
    pdf.add_subclause("7.5", "Restoration: The Lessor reserves the right to require the Lessee to restore the Premises to its original condition at the Lessee's expense. The Lessor shall provide written notice detailing restoration requirements at least 60 days before the lease termination date.")

    pdf.add_clause_heading("8", "UTILITIES AND SERVICES")
    pdf.add_clause_text("The Premises is equipped with a separate electricity meter; the Lessee shall pay electricity consumption charges directly to BESCOM. Water supply is centralized and its cost is included within the CAM Charges. The Lessee is solely responsible for arranging and paying for internet, telephone, and independent security systems. The Lessor provides a backup power generator; however, generator usage by the Lessee shall be metered and charged additionally at Rs. 25 per unit. The Lessee must manage and dispose of all wet and dry waste strictly in accordance with BBMP regulations and guidelines.")

    pdf.add_clause_heading("9", "MAINTENANCE AND REPAIRS")
    pdf.add_subclause("9.1", "Lessee: The Lessee is exclusively responsible for all interior maintenance, non-structural repairs, plumbing and electrical upkeep within the Premises, regular pest control, and the cleaning and maintenance of the kitchen exhaust system, grease traps, and any independent HVAC systems installed within the Premises.")
    pdf.add_subclause("9.2", "Lessor: The Lessor retains responsibility for major structural repairs (including the foundation, external walls, roof, and load-bearing walls), common area maintenance, building facade upkeep, and common plumbing and electrical systems.")
    pdf.add_subclause("9.3", "HVAC: If a central HVAC system serves the building, the Lessee's proportionate share of its maintenance is covered in the CAM Charges. Otherwise, the Lessee must maintain its independent HVAC at its own cost under an annual maintenance contract.")
    pdf.add_subclause("9.4", "Emergency Repairs: In emergency situations where immediate action is required to prevent severe property damage, the Lessee may undertake urgent repairs (up to a limit of Rs. 50,000) and seek reimbursement from the Lessor if the repair falls under the Lessor's responsibilities, provided prior intimation is given to the Lessor wherever practically possible.")

    pdf.add_clause_heading("10", "INSURANCE")
    pdf.add_clause_text("The Lessee is obligated to maintain, at its own cost, comprehensive general liability insurance with a minimum coverage limit of Rs. 1 crore, along with insurance covering its contents, stock, and Trade Fixtures against fire and allied perils. The Lessee must also maintain worker's compensation insurance as legally applicable. The Lessor shall be named as an additional insured on the liability policy. The Lessor is solely responsible for maintaining building structure insurance. Both parties shall provide valid certificates of insurance to each other on an annual basis.")

    pdf.add_clause_heading("11", "LICENSES AND COMPLIANCE")
    pdf.add_clause_text("The Lessee assumes sole and absolute responsibility for obtaining, maintaining, and renewing all licenses and permits required for the Permitted Use. This includes, but is not limited to, the FSSAI license, fire safety No Objection Certificate (NOC) from the Fire Department, trade license from the BBMP, health and sanitation clearances, GST registration, Shop and Establishment registration, lift/escalator certifications (if installed by Lessee), and any required environmental clearances. The Lessor shall provide necessary ownership documents to facilitate these applications.")

    pdf.add_clause_heading("12", "NON-COMPETE BY LESSOR")
    pdf.add_clause_text("During the subsistence of the Lease Term, the Lessor covenants that it shall not lease, let, or permit the use of any other commercial unit within the Horizon Business Centre for the operation of a restaurant, cafe, or food service business that directly competes with the Lessee's primary cuisine category. This exclusivity restriction does not apply to convenience stores, bakeries, or food businesses operating fundamentally different cuisine categories, which the Lessor remains free to accommodate.")

    pdf.add_clause_heading("13", "SIGNAGE")
    pdf.add_clause_text("The Lessee is permitted to install standard business signage on the designated Premises frontage and within the building directory board. All signage installations are strictly subject to the Lessor's prior written approval regarding design, dimensions, and placement. The Lessee must ensure that all signage complies with BBMP municipal regulations and bears all costs associated with installation, licensing, and eventual removal. Upon termination of the lease, the Lessee must remove the signage and repair any damage caused to the building facade.")

    pdf.add_clause_heading("14", "ASSIGNMENT AND SUBLETTING")
    pdf.add_clause_text("The Lessee shall not assign this Lease, sublet the Premises, or part with possession of the whole or any part of the Premises without the prior written consent of the Lessor. The Lessor agrees that such consent shall not be unreasonably withheld if the assignment is to an Affiliate of the Lessee or executed in connection with a bona fide sale of the Lessee's business. In the event of an approved assignment, the original Lessee shall remain liable as a guarantor for the performance of the lease obligations. Subletting or licensing of only a partial area of the Premises is strictly prohibited.")

    pdf.add_clause_heading("15", "DEFAULT AND REMEDIES")
    pdf.add_subclause("15.1", "Events of Default by Lessee: A default occurs if the Lessee fails to pay Rent or charges for 15 days after the due date, breaches any material term and fails to cure it within 30 days of written notice, enters into insolvency or bankruptcy proceedings, assigns the lease without consent, uses the premises for an unpermitted purpose, or abandons the premises for 30 consecutive days.")
    pdf.add_subclause("15.2", "Lessor's Remedies: Upon a Lessee default, the Lessor may terminate the lease, re-enter the premises, recover all arrears along with damages, forfeit the security deposit, and hold the Lessee liable for the rent until the earlier of re-letting the premises or the expiration of the remainder of the lease term (acceleration clause). The Lessor may also recover reasonable legal costs.")
    pdf.add_subclause("15.3", "Events of Default by Lessor: A default occurs if the Lessor fails to make necessary structural repairs within 30 days of written notice, unlawfully interferes with the Lessee's quiet enjoyment of the premises, or fails to refund the security deposit as per the agreed terms.")
    pdf.add_subclause("15.4", "Lessee's Remedies: Upon a Lessor default, the Lessee may set-off documented urgent repair costs against the Rent, seek actual damages, or terminate the lease entirely if the Lessor's material breach remains uncured for a period of 60 days.")

    pdf.add_clause_heading("16", "TERMINATION")
    pdf.add_subclause("16.1", "During Lock-in: If either party terminates the lease during the Lock-in Period for any reason other than a material breach by the other party, such termination shall attract a strict penalty of six (6) months' Rent at the then-applicable rate. Additionally, a termination by the Lessee will result in the forfeiture of the Security Deposit, while an unlawful termination by the Lessor will require a double return of the Security Deposit to the Lessee.")
    pdf.add_subclause("16.2", "After Lock-in: Following the expiration of the Lock-in Period, either party may terminate this Agreement without cause by providing three (3) months' prior written notice to the other party.")
    pdf.add_subclause("16.3", "Mutual: This Lease may be terminated at any time by mutual written and signed agreement between both Parties.")

    pdf.add_clause_heading("17", "SURRENDER AND HANDOVER")
    pdf.add_clause_text("Upon the expiration or earlier termination of the Lease, the Lessee shall surrender and hand over vacant and peaceful possession of the Premises in good and tenantable condition, normal wear and tear excepted. All Lessee's Fixtures must be removed, and the Lessee must arrange for a professional deep cleaning of the Premises. All utility accounts must be settled up to the handover date, and all keys and access cards must be returned. The Lessor shall conduct a joint inspection within seven (7) days of handover. Any dispute regarding the condition of the Premises shall be resolved pursuant to the Dispute Resolution clause.")

    pdf.add_clause_heading("18", "INDEMNIFICATION")
    pdf.add_clause_text("Each party agrees to indemnify, defend, and hold harmless the other party from and against any and all claims, losses, damages, liabilities, and expenses arising from a breach of this Agreement, negligence, or willful misconduct by the indemnifying party or its agents. The Lessee additionally agrees to fully indemnify the Lessor against any claims, actions, or penalties arising from customers, employees, third parties, food safety violations, or environmental regulatory breaches associated with the Lessee's operation of the business on the Premises.")

    pdf.add_clause_heading("19", "FORCE MAJEURE")
    pdf.add_clause_text("Neither party shall be deemed in default if the performance of their obligations is delayed or prevented by events beyond their reasonable control, including acts of God, pandemics, riots, or government mandates. In such events, the affected obligations shall be suspended, and Rent shall be abated proportionally to the period the Premises is rendered unusable. If a Force Majeure event continues for more than 120 consecutive days, either party may terminate the Agreement without penalty.")

    pdf.add_clause_heading("20", "GOVERNING LAW")
    pdf.add_clause_text("This Agreement, and all matters connected with it, shall be governed by and construed in accordance with the laws of the Republic of India, with specific application of the state laws of Karnataka governing commercial tenancies.")

    pdf.add_clause_heading("21", "DISPUTE RESOLUTION")
    pdf.add_clause_text("Any dispute arising out of this Agreement shall first be submitted to good faith negotiation for a period of thirty (30) days. If unresolved, the dispute shall be referred to mediation under the rules of the Indian Institute of Arbitration and Mediation. If mediation fails, the dispute shall be resolved by binding arbitration in accordance with the Arbitration and Conciliation Act, 1996. The arbitral tribunal shall consist of three arbitrators: each party shall appoint one arbitrator, and the two appointed arbitrators shall jointly appoint a presiding third arbitrator. The seat and venue of arbitration shall be Bangalore, the language shall be English, and the arbitral award shall be final and binding on both Parties.")

    pdf.add_clause_heading("22", "NOTICES")
    pdf.add_clause_text("All notices required under this Agreement shall be in writing and delivered by registered post, recognized courier, or email to the registered addresses specified in the preamble. Notices sent by courier shall be deemed received five (5) business days after dispatch. Notices sent by email shall be deemed received immediately upon the sender obtaining a delivery confirmation or read receipt.")

    pdf.add_clause_heading("23", "MISCELLANEOUS")
    pdf.add_clause_text("This Lease Agreement shall be duly registered, and all stamp duty and registration charges shall be borne exclusively by the Lessee. This document constitutes the entire agreement between the Parties and supersedes any prior understandings. Any amendments must be in writing and signed by both Parties. If any provision is found invalid, the remaining provisions shall remain in effect. The failure to enforce any right shall not constitute a waiver. The relationship created by this Agreement is strictly that of a landlord and tenant, and nothing herein shall be construed as creating a partnership or joint venture.")

    pdf.add_schedule_heading("SCHEDULE A: Floor Plan and Premises Description")
    pdf.add_clause_text("Detailed floor plan of Unit GF-04 showing built-up and carpet area boundaries.")

    pdf.add_schedule_heading("SCHEDULE B: Specifications and Condition at Handover")
    pdf.add_clause_text("Detailed list of civil conditions, electrical load capacity, plumbing points, and finishes at the time of handover.")

    pdf.add_schedule_heading("SCHEDULE C: List of Lessor's Fixtures and Equipment")
    pdf.add_clause_text("Inventory of all base structural equipment and permanent fixtures provided by the Lessor.")

    pdf.add_schedule_heading("SCHEDULE D: Maintenance Responsibility Matrix")
    pdf.add_clause_text("Table format detailing specific maintenance items (e.g., HVAC, plumbing, structural cracks) and assigning clear responsibility to either the Lessor or the Lessee.")

    parties = [
        {"name": "Horizon Properties LLP", "rep": "Suresh Reddy", "title": "Partner"},
        {"name": "FreshBite Foods Private Limited", "rep": "Vikram Singh", "title": "Director"}
    ]
    
    # 2 witnesses each
    pdf.ln(10)
    pdf.set_font("Times", "", 11)
    pdf.cell(0, 6, "IN WITNESS WHEREOF, the Parties hereto have executed this Agreement on the date first above written.", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Times", "B", 11)
    pdf.cell(95, 6, f"For and on behalf of {parties[0]['name']}:", ln=False)
    pdf.cell(95, 6, f"For and on behalf of {parties[1]['name']}:", ln=True)
    
    pdf.ln(15)
    
    pdf.set_font("Times", "", 11)
    pdf.cell(95, 6, "_____________________________", ln=False)
    pdf.cell(95, 6, "_____________________________", ln=True)
    
    pdf.cell(95, 6, f"Name: {parties[0]['rep']}", ln=False)
    pdf.cell(95, 6, f"Name: {parties[1]['rep']}", ln=True)
    
    pdf.cell(95, 6, f"Title: {parties[0]['title']}", ln=False)
    pdf.cell(95, 6, f"Title: {parties[1]['title']}", ln=True)
    
    pdf.ln(10)
    
    pdf.set_font("Times", "B", 11)
    pdf.cell(95, 6, "Witness 1 (For Lessor):", ln=False)
    pdf.cell(95, 6, "Witness 1 (For Lessee):", ln=True)
    
    pdf.ln(10)
    
    pdf.set_font("Times", "", 11)
    pdf.cell(95, 6, "_____________________________", ln=False)
    pdf.cell(95, 6, "_____________________________", ln=True)
    
    pdf.cell(95, 6, "Name: _______________________", ln=False)
    pdf.cell(95, 6, "Name: _______________________", ln=True)

    pdf.ln(5)
    
    pdf.set_font("Times", "B", 11)
    pdf.cell(95, 6, "Witness 2 (For Lessor):", ln=False)
    pdf.cell(95, 6, "Witness 2 (For Lessee):", ln=True)
    
    pdf.ln(10)
    
    pdf.set_font("Times", "", 11)
    pdf.cell(95, 6, "_____________________________", ln=False)
    pdf.cell(95, 6, "_____________________________", ln=True)
    
    pdf.cell(95, 6, "Name: _______________________", ln=False)
    pdf.cell(95, 6, "Name: _______________________", ln=True)

    out_path = os.path.join(output_dir, "commercial_lease_agreement.pdf")
    pdf.output(out_path)
    print(f"Generated {out_path} ({pdf.page_no()} pages)")

if __name__ == "__main__":
    output_dir = r"C:\Users\pc\.gemini\antigravity\scratch\production-rag-pipeline\data\sample_pdfs"
    generate_nda(output_dir)
    generate_freelance(output_dir)
    generate_lease(output_dir)
