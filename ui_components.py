import streamlit as st
import textwrap
import json
import datetime
import database
import auth as auth_service
import ai_service


def dedent_html(html_str):
    """Removes leading indentation to prevent markdown code block rendering."""
    return textwrap.dedent(html_str).strip()


def navigate_to(page):
    st.session_state.current_page = page
    st.rerun()


def _greeting() -> str:
    """Returns a time-appropriate greeting based on the local system clock."""
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 17:
        return "Good afternoon"
    elif 17 <= hour < 21:
        return "Good evening"
    else:
        return "Good night"


def _display_name() -> str:
    """Returns the logged-in user's display name from session state."""
    return st.session_state.get("user_name", "Instructor")

# ---------------------------------------------------------------------------
# Top Navigation
# ---------------------------------------------------------------------------

def render_top_nav():
    cols = st.columns([2, 1, 1, 1, 1, 1])
    with cols[0]:
        st.markdown("<h3 style='margin:0; color:#005f73;'>MEDSIM AI</h3>", unsafe_allow_html=True)
    with cols[1]:
        if st.button("Dashboard", use_container_width=True):
            navigate_to("dashboard")
    with cols[2]:
        if st.session_state.get("user_role") == 'instructor':
            if st.button("Create Sim", use_container_width=True):
                navigate_to("create_sim")
    with cols[3]:
        if st.button("My Scenarios", use_container_width=True):
            navigate_to("my_scenarios")
    with cols[4]:
        if st.button("AI Assistant", use_container_width=True):
            navigate_to("assistant")
    with cols[5]:
        if st.button("Logout", use_container_width=True):
            for key in ["user_role", "user_id", "user_name",
                        "sim_stage", "sim_scenario_id", "sim_answer",
                         "sim_saved", "sim_final_score", "sim_feedback"]:
                st.session_state.pop(key, None)
            navigate_to("auth_login")
    st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Auth Pages
# ---------------------------------------------------------------------------

def render_login():
    cols = st.columns([1, 1], gap="large")
    with cols[0]:
        st.markdown(dedent_html("""
        <div class="split-left">
            <h1 class="brand-title">MEDSIM AI</h1>
            <h3 class="brand-subtitle">Synthetic Patient Scenario Studio</h3>
            <p class="brand-desc">"Transform clinical concepts into interactive AI-powered learning simulations."</p>
            <div class="brand-benefits">
                <p>✦ AI-generated fictional cases</p>
                <p>✦ Progressive clinical reasoning</p>
                <p>✦ Intelligent assessment</p>
            </div>
        </div>
        """), unsafe_allow_html=True)
    with cols[1]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("### Sign In")
        email    = st.text_input("Email", placeholder="you@example.com", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Sign In", type="primary", use_container_width=True):
            if not email or not password:
                st.error("Please enter your email and password.")
            else:
                user = auth_service.login_user(email, password)
                if user is None:
                    st.error("Invalid email or password.")
                else:
                    st.session_state.user_id   = user["id"]
                    st.session_state.user_role = user["role"]
                    st.session_state.user_name = user["full_name"]
                    navigate_to("dashboard")

        st.markdown("---")
        st.markdown("Don't have an account?")
        if st.button("Create Account", use_container_width=True):
            navigate_to("auth_register")


def render_register():
    cols = st.columns([1, 1], gap="large")
    with cols[0]:
        st.markdown(dedent_html("""
        <div class="split-left">
            <h1 class="brand-title">MEDSIM AI</h1>
            <h3 class="brand-subtitle">Synthetic Patient Scenario Studio</h3>
            <p class="brand-desc">"Transform clinical concepts into interactive AI-powered learning simulations."</p>
            <div class="brand-benefits">
                <p>✦ AI-generated fictional cases</p>
                <p>✦ Progressive clinical reasoning</p>
                <p>✦ Intelligent assessment</p>
            </div>
        </div>
        """), unsafe_allow_html=True)
    with cols[1]:
        st.markdown("### Sign Up")
        name     = st.text_input("Full Name",         key="reg_name")
        email    = st.text_input("Email",             key="reg_email")
        password = st.text_input("Password",          type="password", key="reg_pw")
        confirm  = st.text_input("Confirm Password",  type="password", key="reg_pw2")
        role     = st.selectbox("Role", ["Instructor", "Student"], key="reg_role")

        if st.button("Create Account", type="primary", use_container_width=True):
            if not name or not email or not password or not confirm:
                st.error("Please fill in all fields.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                user = auth_service.register_user(name, email, password, role.lower())
                if user is None:
                    st.error("An account with this email already exists.")
                else:
                    st.session_state.user_id   = user["id"]
                    st.session_state.user_role = user["role"]
                    st.session_state.user_name = user["full_name"]
                    st.success("Account created! Redirecting…")
                    navigate_to("dashboard")

        st.markdown("---")
        st.markdown("Already have an account?")
        if st.button("Sign In", use_container_width=True):
            navigate_to("auth_login")

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def render_dashboard(role):
    if role == 'instructor':
        _render_instructor_dashboard()
    else:
        _render_student_dashboard()


def _render_instructor_dashboard():
    greeting = _greeting()
    name = st.session_state.get("user_name", "Instructor")
    st.markdown(f"## {greeting}, {name}")
    st.markdown("Create engaging clinical simulations with AI.")

    st.markdown(dedent_html("""
    <div class="med-card" style="background-color: #f0fdfa; border-left-color: #0d9488;">
        <h3>CREATE NEW SIMULATION</h3>
        <p>Generate a fictional clinical case</p>
    </div>
    """), unsafe_allow_html=True)
    if st.button("✦ Create Simulation", type="primary"):
        navigate_to("create_sim")

    st.markdown("---")
    st.markdown("### Statistics")

    instructor_id = st.session_state.get("user_id")
    if instructor_id is not None:
        stats = database.get_instructor_stats(instructor_id)
        total_scenarios  = stats["total_scenarios"]
        published_cases  = stats["published_cases"]
        student_attempts = stats["student_attempts"]
        avg_score        = f"{stats['avg_score']}%" if stats["avg_score"] else "N/A"
    else:
        total_scenarios = published_cases = student_attempts = 0
        avg_score = "N/A"

    stat_cols = st.columns(4)
    stat_cols[0].metric("Total Scenarios",  total_scenarios)
    stat_cols[1].metric("Published Cases",  published_cases)
    stat_cols[2].metric("Student Attempts", student_attempts)
    stat_cols[3].metric("Average Score",    avg_score)

    st.markdown("---")
    st.markdown("### Recent Scenarios")

    if instructor_id is not None:
        scenarios = database.get_instructor_scenarios(instructor_id)
    else:
        scenarios = []

    if scenarios:
        for sc in scenarios[:5]:
            status_label = "✅ Published" if sc["published"] else "📝 Draft"
            created = sc["created_at"][:10] if sc["created_at"] else "—"
            st.markdown(dedent_html(f"""
            <div class="med-card">
                <h4>{sc['title']}</h4>
                <p>{sc['specialty']} | {sc['difficulty']} | {sc['learner_level']} | {status_label} | Created: {created}</p>
            </div>
            """), unsafe_allow_html=True)
            c1, c2, _ = st.columns([1, 1, 5])
            if c1.button("Open", key=f"dash_open_{sc['id']}"):
                st.session_state.view_scenario_id = sc["id"]
                navigate_to("review_sim")
            if c2.button("My Scenarios", key=f"dash_my_{sc['id']}"):
                navigate_to("my_scenarios")
    else:
        st.info("No scenarios yet. Click 'Create Simulation' to get started.")


def _render_student_dashboard():
    greeting = _greeting()
    name = st.session_state.get("user_name", "Student")
    st.markdown(f"## {greeting}, {name}!")
    st.markdown("Choose a simulation and start practising your clinical reasoning.")

    st.markdown("### Available Simulations")
    published = database.get_published_scenarios()

    if published:
        for sc in published:
            st.markdown(dedent_html(f"""
            <div class="med-card">
                <h4>{sc['title']}</h4>
                <p>
                    <strong>Specialty:</strong> {sc['specialty']} &nbsp;|&nbsp;
                    <strong>Difficulty:</strong> {sc['difficulty']} &nbsp;|&nbsp;
                    <strong>Level:</strong> {sc['learner_level']} &nbsp;|&nbsp;
                    <strong>Objective:</strong> {sc['learning_objective']}
                </p>
            </div>
            """), unsafe_allow_html=True)
            if st.button("Start Simulation", key=f"start_{sc['id']}", type="primary"):
                st.session_state.sim_scenario_id = sc["id"]
                st.session_state.sim_stage = 1
                st.session_state.pop("sim_answer", None)
                st.session_state.pop("sim_saved", None)
                st.session_state.pop("sim_final_score", None)
                navigate_to("play_sim")
    else:
        st.info("No simulations are published yet. Check back later.")

    st.markdown("---")
    st.markdown("### Your Progress")

    student_id = st.session_state.get("user_id")
    if student_id is not None:
        stu_stats = database.get_student_stats(student_id)
        completed = stu_stats["completed"]
        avg_sc    = f"{stu_stats['avg_score']}%" if stu_stats["avg_score"] is not None else "N/A"
    else:
        completed = 0
        avg_sc    = "N/A"

    stat_cols = st.columns(3)
    stat_cols[0].metric("Completed Simulations", completed)
    stat_cols[1].metric("Average Score",          avg_sc)
    stat_cols[2].metric("Status",                 "Active" if completed > 0 else "—")

    # Recent completed sessions
    if student_id is not None:
        sessions = database.get_student_sessions(student_id)
        if sessions:
            st.markdown("#### Recent Results")
            for s in sessions[:5]:
                created = s["created_at"][:10] if s["created_at"] else "—"
                score_str = f"{s['score']}%" if s["score"] is not None else "—"
                st.markdown(dedent_html(f"""
                <div class="med-card">
                    <p><strong>{s['title']}</strong> — {s['specialty']} | {s['difficulty']} |
                    Score: {score_str} | Completed: {created}</p>
                </div>
                """), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# My Scenarios
# ---------------------------------------------------------------------------

def render_my_scenarios():
    st.markdown("## My Scenarios")
    st.markdown("Manage all scenarios you have created.")

    instructor_id = st.session_state.get("user_id")

    if instructor_id is None:
        st.warning(
            "You are not logged in to a database account. "
            "Please log out and sign in with a registered account."
        )
        return

    scenarios = database.get_instructor_scenarios(instructor_id)

    if not scenarios:
        st.info("You have not created any scenarios yet.")
        if st.button("✦ Create Your First Simulation", type="primary"):
            navigate_to("create_sim")
        return

    for sc in scenarios:
        status_label = "✅ Published" if sc["published"] else "📝 Draft"
        created = sc["created_at"][:10] if sc["created_at"] else "—"

        st.markdown(dedent_html(f"""
        <div class="med-card">
            <h4>{sc['title']}</h4>
            <p>
                <strong>Specialty:</strong> {sc['specialty']} &nbsp;|&nbsp;
                <strong>Level:</strong> {sc['learner_level']} &nbsp;|&nbsp;
                <strong>Difficulty:</strong> {sc['difficulty']} &nbsp;|&nbsp;
                <strong>Status:</strong> {status_label} &nbsp;|&nbsp;
                <strong>Created:</strong> {created}
            </p>
        </div>
        """), unsafe_allow_html=True)

        pub_label = "Unpublish" if sc["published"] else "Publish"
        c1, c2, c3, c4, _ = st.columns([1, 1, 1, 1, 3])

        if c1.button("Open", key=f"ms_open_{sc['id']}"):
            st.session_state.view_scenario_id = sc["id"]
            navigate_to("review_sim")

        c2.button("Edit", key=f"ms_edit_{sc['id']}")  # reserved for future edit page

        if c3.button(pub_label, key=f"ms_pub_{sc['id']}"):
            database.toggle_publish_scenario(sc["id"], instructor_id)
            st.rerun()

        if c4.button("Delete", key=f"ms_del_{sc['id']}"):
            database.delete_scenario(sc["id"], instructor_id)
            st.rerun()

# ---------------------------------------------------------------------------
# Create Simulation
# ---------------------------------------------------------------------------

SPECIALTIES  = ["Cardiology", "Neurology", "Pulmonology", "Pediatrics",
                 "General Medicine", "Emergency Medicine", "Gastroenterology",
                 "Nephrology", "Endocrinology", "Infectious Disease"]
LEVELS       = ["Beginner", "Intermediate", "Advanced"]
CASE_TYPES   = ["Routine Case", "Emergency Case", "Diagnostic Challenge", "Hidden Diagnosis"]
OBJECTIVES   = ["Clinical Reasoning", "Patient Assessment", "Differential Diagnosis",
                 "Investigation Interpretation", "Treatment Planning"]
DIFFICULTIES = ["Easy", "Medium", "Hard"]


def render_create_simulation():
    st.markdown("## Create New Simulation")

    st.markdown(dedent_html("""
    <div style="
        background: linear-gradient(135deg, #e6fffb, #f0f9ff);
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #b2dfdb;
        margin-bottom: 25px;">
        <h3 style="margin:0; color:#0f766e;">✦ AI Clinical Scenario Generator</h3>
        <p style="color:#475569; margin:8px 0 0 0;">
            Configure the case and generate a complete fictional patient scenario.
        </p>
    </div>
    """), unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        specialty = st.selectbox("SPECIALTY", SPECIALTIES, key="cs_specialty")
        level = st.selectbox("LEARNER LEVEL", LEVELS, key="cs_level")
        case_type = st.selectbox("CASE TYPE", CASE_TYPES, key="cs_case_type")

    with col2:
        objective = st.selectbox("LEARNING OBJECTIVE", OBJECTIVES, key="cs_objective")
        difficulty = st.selectbox("DIFFICULTY", DIFFICULTIES, key="cs_difficulty")
        extra = st.text_input(
            "Additional Teaching Focus (Optional)",
            key="cs_extra"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("✦ Generate Simulation", type="primary", use_container_width=True):
        config = {
            "specialty": specialty,
            "level": level,
            "case_type": case_type,
            "objective": objective,
            "difficulty": difficulty,
            "extra": extra,
        }

        with st.spinner("Generating the clinical scenario..."):
            try:
                result = ai_service.generate_scenario(
                    specialty=specialty,
                    learner_level=level,
                    objective=objective,
                    difficulty=difficulty,
                    case_type=case_type,
                )

                # Convert Pydantic Scenario to a DB-friendly dictionary.
                if result is not None:
                    if hasattr(result, "model_dump"):
                        obj = result.model_dump()
                    elif hasattr(result, "dict"):
                        obj = result.dict()
                    elif isinstance(result, dict):
                        obj = result
                    else:
                        obj = None

                    if obj:
                        profile = obj.get("profile", {})
                        vitals = obj.get("vital_signs", {})
                        questions = obj.get("questions", [])

                        scenario_data = {
                            "patient_name": profile.get("name", "Fictional Patient"),
                            "age": profile.get("age", "—"),
                            "gender": profile.get("gender", "—"),
                            "occupation": profile.get("occupation", "—"),
                            "past_medical_history": profile.get(
                                "past_medical_history", []
                            ),
                            "chief_complaint": obj.get("chief_complaint", "—"),
                            "presentation": obj.get("initial_presentation", "—"),
                            "bp": vitals.get("blood_pressure", "—"),
                            "hr": vitals.get("heart_rate", "—"),
                            "temp": vitals.get("temperature", "—"),
                            "rr": vitals.get("respiratory_rate", "—"),
                            "spo2": vitals.get("oxygen_saturation", "—"),
                            "investigations": obj.get("investigation_results", "—"),
                            "hidden_diagnosis": obj.get("hidden_diagnosis", "—"),
                            "expected_answer": "\n\n".join(
                                q.get("expected_answer", "")
                                for q in questions
                                if isinstance(q, dict)
                            ) or "—",
                            "rubric": "\n\n".join(
                                q.get("scoring_guidance", "")
                                for q in questions
                                if isinstance(q, dict)
                            ) or "—",
                            "questions": questions,
                            "instructor_notes": obj.get(
                                "instructor_notes", extra
                            ),
                        }

                        st.session_state.pending_scenario_config = config
                        st.session_state.pending_scenario_data = scenario_data
                        st.session_state.pop("view_scenario_id", None)
                        navigate_to("review_sim")
                    else:
                        raise ValueError("AI returned an empty scenario.")
                else:
                    raise ValueError("AI scenario generation returned no data.")

            except Exception as e:
                # Keep the demo usable if Gemini is unavailable/quota-limited.
                # The app clearly labels this as a fallback fictional case.
                st.warning(
                    "AI generation is temporarily unavailable. "
                    "A complete demo scenario has been prepared so you can continue testing."
                )
                st.session_state.pending_scenario_config = config
                st.session_state.pending_scenario_data = _build_fallback_scenario(config)
                st.session_state.pop("view_scenario_id", None)
                navigate_to("review_sim")


def _build_fallback_scenario(config: dict) -> dict:
    """
    Local demo scenarios used only when Gemini is unavailable.
    They vary by specialty so repeated demos do not always show Alex Morgan.
    """
    specialty = config.get("specialty", "Emergency Medicine")

    cases = {
        "Emergency Medicine": {
            "patient_name": "Priya Nair", "age": 29, "gender": "Female",
            "occupation": "Software Engineer", "past_medical_history": ["Asthma"],
            "chief_complaint": "Worsening shortness of breath and wheezing",
            "presentation": "A 29-year-old woman presents with increasing breathlessness and wheezing since this morning. She reports exposure to dust while cleaning her apartment. She is speaking in short sentences.",
            "bp": "132/84 mmHg", "hr": "112 bpm", "temp": "37.0 °C", "rr": "28 /min", "spo2": "89%",
            "investigations": "Peak expiratory flow is reduced compared with her usual value. Consider pulse oximetry and appropriate respiratory assessment.",
            "hidden_diagnosis": "Acute asthma exacerbation",
            "expected_answer": "Acute asthma exacerbation is likely because of wheezing, shortness of breath, reduced oxygen saturation and a known history of asthma. Assess severity and response to appropriate emergency management.",
            "rubric": "Clinical reasoning 40 points; recognition of asthma features 25 points; severity assessment 25 points; clear explanation 10 points.",
            "instructor_notes": "Focus on recognizing an acute asthma pattern and assessing severity."
        },
        "Cardiology": {
            "patient_name": "Rahul Mehta", "age": 58, "gender": "Male",
            "occupation": "Bank Manager", "past_medical_history": ["Hypertension", "High cholesterol"],
            "chief_complaint": "Pressure-like chest discomfort",
            "presentation": "A 58-year-old man develops central chest pressure while climbing stairs. The discomfort has lasted 20 minutes and is associated with sweating and nausea.",
            "bp": "156/94 mmHg", "hr": "104 bpm", "temp": "36.7 °C", "rr": "22 /min", "spo2": "94%",
            "investigations": "Initial evaluation should include an ECG and appropriate cardiac blood testing, interpreted in the context of the clinical presentation.",
            "hidden_diagnosis": "Acute coronary syndrome",
            "expected_answer": "Acute coronary syndrome should be considered because of exertional pressure-like chest discomfort with sweating and nausea plus cardiovascular risk factors. The next evaluation should include an ECG and appropriate cardiac biomarkers.",
            "rubric": "Clinical reasoning 40 points; recognition of ACS features 25 points; appropriate investigations 25 points; explanation 10 points.",
            "instructor_notes": "Focus on recognizing concerning chest-pain features and choosing appropriate initial investigations."
        },
        "Neurology": {
            "patient_name": "Daniel Thomas", "age": 67, "gender": "Male",
            "occupation": "Retired Teacher", "past_medical_history": ["Atrial fibrillation"],
            "chief_complaint": "Sudden difficulty speaking",
            "presentation": "A 67-year-old man suddenly develops difficulty speaking and weakness of his right arm while having breakfast. His family reports that he was normal earlier this morning.",
            "bp": "174/98 mmHg", "hr": "96 bpm", "temp": "36.6 °C", "rr": "18 /min", "spo2": "97%",
            "investigations": "Urgent neurological assessment and brain imaging are required to distinguish major causes of an acute focal neurological deficit.",
            "hidden_diagnosis": "Acute ischemic stroke",
            "expected_answer": "Acute stroke should be suspected because the neurological deficits began suddenly and are focal. The patient needs urgent neurological assessment and appropriate brain imaging.",
            "rubric": "Clinical reasoning 40 points; recognition of sudden focal deficit 25 points; appropriate urgent investigation 25 points; explanation 10 points.",
            "instructor_notes": "Focus on identifying a sudden focal neurological deficit and the need for urgent evaluation."
        },
        "Pediatrics": {
            "patient_name": "Aarav Sharma", "age": 7, "gender": "Male",
            "occupation": "School Student", "past_medical_history": ["No significant history"],
            "chief_complaint": "Fever and sore throat",
            "presentation": "A 7-year-old boy has fever, painful swallowing and sore throat for two days. He has reduced appetite but is drinking fluids.",
            "bp": "104/68 mmHg", "hr": "108 bpm", "temp": "38.6 °C", "rr": "22 /min", "spo2": "98%",
            "investigations": "Clinical throat examination and an appropriate test for suspected streptococcal infection may be considered based on the clinical assessment.",
            "hidden_diagnosis": "Streptococcal pharyngitis",
            "expected_answer": "Streptococcal pharyngitis should be considered based on fever, sore throat and painful swallowing. The next step is a focused examination and an appropriate diagnostic test when indicated.",
            "rubric": "Clinical reasoning 40 points; recognition of relevant symptoms 25 points; appropriate assessment/testing 25 points; explanation 10 points.",
            "instructor_notes": "Focus on symptom interpretation and choosing an appropriate diagnostic approach."
        },
        "Pulmonology": {
            "patient_name": "Meera Rao", "age": 45, "gender": "Female",
            "occupation": "Teacher", "past_medical_history": ["No significant history"],
            "chief_complaint": "Sudden shortness of breath",
            "presentation": "A 45-year-old woman develops sudden shortness of breath after returning from a long international flight. She feels anxious and has mild chest discomfort.",
            "bp": "142/88 mmHg", "hr": "108 bpm", "temp": "36.8 °C", "rr": "25 /min", "spo2": "92%",
            "investigations": "Assess clinical probability and consider appropriate blood testing and imaging for suspected venous thromboembolism.",
            "hidden_diagnosis": "Pulmonary embolism",
            "expected_answer": "Pulmonary embolism should be considered because of sudden dyspnea, tachycardia, reduced oxygen saturation and recent prolonged travel. Further assessment should be guided by clinical probability and appropriate investigations.",
            "rubric": "Clinical reasoning 40 points; recognition of risk factors 25 points; investigation selection 25 points; explanation 10 points.",
            "instructor_notes": "Focus on linking sudden symptoms and risk factors to the diagnostic reasoning."
        },
    }

    case = cases.get(specialty, cases["Emergency Medicine"]).copy()
    case["instructor_notes"] = (
        f"{case['instructor_notes']} "
        f"Configured for {config.get('level', 'Intermediate')} level, "
        f"{config.get('difficulty', 'Medium')} difficulty and "
        f"{config.get('objective', 'Clinical Reasoning')}."
    )
    case["questions"] = [{
        "question_text": "What is your working diagnosis and what would you investigate or assess next?",
        "expected_answer": case["expected_answer"],
        "scoring_guidance": case["rubric"],
    }]
    return case


# ---------------------------------------------------------------------------
# Review Simulation
# ---------------------------------------------------------------------------

def render_review_simulation():
    st.markdown("## Review Generated Scenario")

    st.markdown(dedent_html("""
    <div style="display:flex; justify-content:space-between; margin-bottom:30px;
                border-bottom:1px solid #e2e8f0; padding-bottom:10px;">
        <span style="color:#64748b;">01 Configure</span>
        <span style="font-weight:bold; color:#008080;">02 Generate</span>
        <span style="font-weight:bold; color:#008080;">03 Review</span>
        <span style="color:#64748b;">04 Publish</span>
    </div>
    """), unsafe_allow_html=True)

    instructor_id = st.session_state.get("user_id")

    # Existing saved scenario.
    view_id = st.session_state.get("view_scenario_id")
    if view_id is not None:
        sc = database.get_scenario_by_id(view_id)
        if sc is None:
            st.error("Scenario not found.")
            return
        _display_scenario_review(sc, instructor_id, saved=True)
        return

    config = st.session_state.get("pending_scenario_config")
    data = st.session_state.get("pending_scenario_data")

    if config is None or data is None:
        st.warning("No scenario to review. Please create a simulation first.")
        if st.button("← Back to Create"):
            navigate_to("create_sim")
        return

    sc = {
        "id": None,
        "title": f"{config['specialty']} – {config['case_type']}",
        "specialty": config["specialty"],
        "learner_level": config["level"],
        "learning_objective": config["objective"],
        "difficulty": config["difficulty"],
        "case_type": config["case_type"],
        "published": False,
        "created_at": None,
        "scenario_data": json.dumps(data),
    }

    _display_scenario_review(sc, instructor_id, saved=False, config=config)


def _display_scenario_review(sc: dict, instructor_id, saved: bool, config: dict = None):
    """Renders the scenario review cards and Save/Publish buttons."""
    try:
        data = json.loads(sc.get("scenario_data", "{}"))
    except (json.JSONDecodeError, TypeError):
        data = {}

    # Repair legacy placeholder scenarios created before AI generation was wired in.
    # This prevents old database records containing "To be generated by AI" / "—"
    # from appearing blank in the mentor demo.
    placeholder_markers = {"To be generated by AI", "AI scenario generation will populate this field.", "—"}
    if (not data or
        data.get("patient_name") in (None, "", "Fictional Patient") and
        data.get("chief_complaint") in placeholder_markers):
        fallback_cfg = {
            "specialty": sc.get("specialty", "Emergency Medicine"),
            "case_type": sc.get("case_type", "Emergency Case"),
            "level": sc.get("learner_level", "Intermediate"),
            "objective": sc.get("learning_objective", "Clinical Reasoning"),
            "difficulty": sc.get("difficulty", "Medium"),
            "extra": "Recognize risk factors, interpret symptoms and vital signs, and select appropriate investigations."
        }
        data = _build_fallback_scenario(fallback_cfg)

    st.markdown(f"### Scenario: {sc.get('title', '—')}")
    st.markdown(dedent_html(f"""
    <div class="med-card">
        <p>
            <strong>Specialty:</strong> {sc.get('specialty','—')} &nbsp;|&nbsp;
            <strong>Level:</strong> {sc.get('learner_level','—')} &nbsp;|&nbsp;
            <strong>Difficulty:</strong> {sc.get('difficulty','—')} &nbsp;|&nbsp;
            <strong>Objective:</strong> {sc.get('learning_objective','—')}
        </p>
    </div>
    """), unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("#### Patient Profile")
        st.markdown(dedent_html(f"""
        <div class="med-card">
            <p>
                <strong>Name:</strong> {data.get('patient_name','—')} &nbsp;|&nbsp;
                <strong>Age:</strong> {data.get('age','—')} &nbsp;|&nbsp;
                <strong>Gender:</strong> {data.get('gender','—')} &nbsp;|&nbsp;
                <strong>Occupation:</strong> {data.get('occupation','—')}
            </p>
        </div>
        """), unsafe_allow_html=True)

        st.markdown("#### Case Structure")
        st.info(f"**Chief Complaint:** {data.get('chief_complaint', '—')}")
        st.info(f"**Initial Presentation:** {data.get('presentation', '—')}")

        st.markdown("#### Vital Signs")
        st.markdown(dedent_html(f"""
        <div class="med-card" style="padding: 15px;">
            BP: {data.get('bp','—')} &nbsp; HR: {data.get('hr','—')} &nbsp;
            Temp: {data.get('temp','—')} &nbsp; RR: {data.get('rr','—')} &nbsp;
            SpO2: {data.get('spo2','—')}
        </div>
        """), unsafe_allow_html=True)

        st.markdown("#### Investigations")
        st.info(data.get("investigations", "—"))

    with col2:
        st.markdown("#### Instructor Data (Hidden from Student)")
        st.warning(f"**Hidden Diagnosis:** {data.get('hidden_diagnosis','—')}")
        st.success(f"**Expected Answers:** {data.get('expected_answer','—')}")
        st.info(f"**Assessment Rubric:** {data.get('rubric','—')}")
        st.text_area("Instructor Notes", value=data.get("instructor_notes", ""), key="review_notes")

    st.markdown("<br>", unsafe_allow_html=True)

    if saved:
        # Already in the DB — show publish toggle and back
        is_pub = bool(sc.get("published"))
        c1, c2, c3, _ = st.columns([1, 1, 1, 3])
        with c1:
            if st.button("← Back to My Scenarios"):
                navigate_to("my_scenarios")
        with c2:
            pub_lbl = "Unpublish" if is_pub else "Publish"
            if st.button(pub_lbl, type="primary", use_container_width=True):
                if instructor_id:
                    database.toggle_publish_scenario(sc["id"], instructor_id)
                    st.success("Status updated.")
                    st.rerun()
        with c3:
            if st.button("Delete Scenario", use_container_width=True):
                if instructor_id:
                    database.delete_scenario(sc["id"], instructor_id)
                    st.success("Scenario deleted.")
                    st.session_state.pop("view_scenario_id", None)
                    navigate_to("my_scenarios")
    else:
        # New scenario — offer Save Draft and Publish
        c1, c2, _ = st.columns([1, 1, 2])
        with c1:
            if st.button("Save Draft", use_container_width=True):
                if instructor_id is None:
                    st.error("You must be logged in to save a scenario.")
                else:
                    _persist_scenario(sc, instructor_id, published=False)
                    st.success("Scenario saved as draft.")
                    st.session_state.pop("pending_scenario_config", None)
                    navigate_to("my_scenarios")
        with c2:
            if st.button("Publish Scenario", type="primary", use_container_width=True):
                if instructor_id is None:
                    st.error("You must be logged in to publish a scenario.")
                else:
                    _persist_scenario(sc, instructor_id, published=True)
                    st.success("Scenario published.")
                    st.session_state.pop("pending_scenario_config", None)
                    navigate_to("my_scenarios")


def _persist_scenario(sc: dict, instructor_id: int, published: bool) -> int:
    """Saves the scenario to SQLite and returns the new scenario id."""
    return database.save_scenario(
        instructor_id    = instructor_id,
        title            = sc["title"],
        specialty        = sc["specialty"],
        learner_level    = sc["learner_level"],
        learning_objective = sc["learning_objective"],
        difficulty       = sc["difficulty"],
        case_type        = sc["case_type"],
        scenario_data    = sc.get("scenario_data", "{}"),
        published        = published,
    )

# ---------------------------------------------------------------------------
# Simulation Player  (Student — progressive reveal)
# ---------------------------------------------------------------------------

def render_simulation_player():
    scenario_id = st.session_state.get("sim_scenario_id")
    if scenario_id is None:
        st.warning("No simulation selected. Please choose one from your dashboard.")
        if st.button("← Back to Dashboard"):
            navigate_to("dashboard")
        return

    sc = database.get_scenario_by_id(scenario_id)
    if sc is None:
        st.error("Simulation not found.")
        navigate_to("dashboard")
        return

    try:
        data = json.loads(sc.get("scenario_data", "{}"))
    except (json.JSONDecodeError, TypeError):
        data = {}

    # Repair old placeholder scenarios when a student opens them.
    placeholder_markers = {
        "To be generated by AI",
        "AI scenario generation will populate this field.",
        "—",
        "",
        None,
    }
    if (
        not data
        or data.get("patient_name") in {"Fictional Patient", None, ""}
        or data.get("chief_complaint") in placeholder_markers
    ):
        legacy_config = {
            "specialty": sc.get("specialty", "Emergency Medicine"),
            "case_type": sc.get("case_type", "Emergency Case"),
            "level": sc.get("learner_level", "Intermediate"),
            "objective": sc.get("learning_objective", "Clinical Reasoning"),
            "difficulty": sc.get("difficulty", "Medium"),
        }
        data = _build_fallback_scenario(legacy_config)

    stage = st.session_state.get("sim_stage", 1)

    # Stage progress bar
    stage_labels = ["Patient Profile", "Presentation", "Investigations", "Reasoning", "Assessment"]
    st.markdown(dedent_html(f"""
    <div style="display:flex; gap: 15px; margin-bottom: 20px;
                border-bottom: 1px solid #e2e8f0; padding-bottom: 10px;">
        {''.join(
            f'<span style="font-weight:bold; color:#008080;">● {lbl}</span>'
            if i < stage else
            f'<span style="color:#64748b;">○ {lbl}</span>'
            for i, lbl in enumerate(stage_labels, start=1)
        )}
    </div>
    """), unsafe_allow_html=True)

    st.markdown(dedent_html("""
    <div style="display:inline-block; background:#e0f2fe; color:#0369a1;
                padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;
                font-weight: 600; margin-bottom: 16px;">
        🧪 SYNTHETIC PATIENT — Fictional scenario for educational purposes only
    </div>
    """), unsafe_allow_html=True)

    # ----- STAGE 1: Patient Profile + Chief Complaint -----
    if stage == 1:
        st.markdown("### Stage 1 — Patient Profile & Chief Complaint")
        st.markdown(dedent_html(f"""
        <div class="med-card">
            <h4>Patient: {data.get('patient_name','—')}, {data.get('age','—')}</h4>
            <p><strong>Gender:</strong> {data.get('gender','—')} &nbsp;|&nbsp;
               <strong>Occupation:</strong> {data.get('occupation','—')}</p>
            <p><strong>Chief Complaint:</strong> {data.get('chief_complaint','—')}</p>
        </div>
        """), unsafe_allow_html=True)
        if st.button("Continue to Clinical Presentation →", type="primary"):
            st.session_state.sim_stage = 2
            st.rerun()

    # ----- STAGE 2: Presentation + Vital Signs -----
    elif stage == 2:
        st.markdown("### Stage 2 — Clinical Presentation & Vital Signs")
        st.info(f"**Initial Presentation:** {data.get('presentation','—')}")
        st.markdown(dedent_html(f"""
        <div class="med-card" style="padding: 15px;">
            <strong>Vital Signs</strong><br>
            BP: {data.get('bp','—')} &nbsp; HR: {data.get('hr','—')} &nbsp;
            Temp: {data.get('temp','—')} &nbsp; RR: {data.get('rr','—')} &nbsp;
            SpO2: {data.get('spo2','—')}
        </div>
        """), unsafe_allow_html=True)
        if st.button("Continue to Investigations →", type="primary"):
            st.session_state.sim_stage = 3
            st.rerun()

    # ----- STAGE 3: Investigations + Reasoning question -----
    elif stage == 3:
        st.markdown("### Stage 3 — Investigation Results")
        st.info(f"**Investigations:** {data.get('investigations','—')}")
        st.markdown("---")
        st.markdown("### Think like a clinician.")
        st.markdown("**Based on the above, what is your working diagnosis and what would you do next?**")
        answer = st.text_area("Your clinical reasoning…", height=180, key="student_answer_input")
        if st.button("Submit Clinical Reasoning", type="primary"):
            if not answer.strip():
                st.warning("Please enter your reasoning before submitting.")
            else:
                st.session_state.sim_answer = answer.strip()
                st.session_state.sim_stage = 4
                st.rerun()

    # ----- STAGE 4: AI/local evaluation + persistence -----
    elif stage >= 4:
        if not st.session_state.get("sim_saved"):
            student_id = st.session_state.get("user_id")
            answer = st.session_state.get("sim_answer", "")

            expected = data.get("expected_answer", "")
            rubric = data.get("rubric", "")

            with st.spinner("Evaluating your clinical reasoning..."):
                feedback = ai_service.evaluate_student_answer(
                    student_answer=answer,
                    expected_answer=expected,
                    rubric=rubric,
                )

            import re
            match = re.search(r"SCORE\s*:\s*(\d{1,3})", feedback or "", re.IGNORECASE)
            score = max(0, min(100, int(match.group(1)))) if match else 0

            if student_id and scenario_id:
                database.save_session(student_id, scenario_id, score)

            st.session_state.sim_saved = True
            st.session_state.sim_final_score = score
            st.session_state.sim_feedback = feedback

        navigate_to("results")


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

def render_results():
    score = st.session_state.get("sim_final_score", 0)
    answer = st.session_state.get("sim_answer", "")
    feedback = st.session_state.get("sim_feedback", "")

    st.markdown("## Simulation Complete ✓")
    st.markdown(dedent_html(f"""
    <div style="text-align:center; padding: 40px; background-color:#f0fdfa;
                border-radius:12px; margin-bottom: 30px; border: 1px solid #ccfbf1;">
        <h1 style="font-size:4rem; color:#0d9488; margin:0;">{score}%</h1>
        <p style="font-size:1.2rem; color:#0f766e; font-weight:600;">Overall Score</p>
    </div>
    """), unsafe_allow_html=True)

    scenario_id = st.session_state.get("sim_scenario_id")
    sc = database.get_scenario_by_id(scenario_id) if scenario_id else None
    try:
        data = json.loads(sc.get("scenario_data", "{}")) if sc else {}
    except (json.JSONDecodeError, TypeError):
        data = {}

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown("### Your Answer")
        if answer:
            st.markdown(dedent_html(f"""
            <div class="med-card" style="min-height: 100px;">
                <p>{answer}</p>
            </div>
            """), unsafe_allow_html=True)
        else:
            st.info("No answer recorded.")

    with col2:
        st.markdown("### Expected Reasoning")
        st.info(data.get("expected_answer", "—"))

    st.markdown("---")
    st.markdown("### AI Evaluation")
    if feedback:
        # Hide the machine-readable SCORE line because the score is already
        # shown prominently above.
        clean_feedback = __import__("re").sub(
            r"SCORE\s*:\s*\d{1,3}\s*\n?",
            "",
            feedback,
            count=1,
            flags=__import__("re").IGNORECASE,
        ).strip()
        st.markdown(clean_feedback)
    else:
        st.info("No evaluation feedback available.")

    st.markdown("---")
    st.markdown("### Case Details")
    st.info(f"**Final Diagnosis:** {data.get('hidden_diagnosis','—')}")
    st.success("Your attempt has been saved to your progress.")
    st.info(f"**Teaching Point:** {data.get('instructor_notes','—')}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Try Another Simulation", type="primary"):
        for key in [
            "sim_stage", "sim_scenario_id", "sim_answer",
            "sim_saved", "sim_final_score", "sim_feedback"
        ]:
            st.session_state.pop(key, None)
        navigate_to("dashboard")


# ---------------------------------------------------------------------------
# AI Assistant
# ---------------------------------------------------------------------------

def render_assistant():
    st.markdown("## MedSim Assistant")
    st.markdown("*Your AI guide for simulation-based learning.*")

    st.markdown(dedent_html("""
    <div class="safety-banner" style="margin-bottom: 30px;">
        <p style="margin:0;"><strong>Note:</strong> I am an educational assistant.
        I do not diagnose real patients or provide personalized medical advice.
        I only assist with educational simulation content.</p>
    </div>
    """), unsafe_allow_html=True)

    st.markdown("### Quick Actions")
    cols = st.columns(3)
    cols[0].button("How do I create a case?",          use_container_width=True, key="qa_1")
    cols[1].button("Explain this simulation",           use_container_width=True, key="qa_2")
    cols[2].button("Suggest a learning objective",      use_container_width=True, key="qa_3")
    cols[0].button("How can I increase difficulty?",    use_container_width=True, key="qa_4")
    cols[1].button("Why was my answer scored this way?",use_container_width=True, key="qa_5")
    cols[2].button("Help me troubleshoot",              use_container_width=True, key="qa_6")

    st.markdown("---")
    st.markdown("### Chat")

    st.markdown(dedent_html("""
    <div style="background-color:#f8f9fa; padding:20px; border-radius:12px;
                height: 250px; overflow-y:auto; margin-bottom:20px;
                border: 1px solid #e2e8f0;">
        <div style="margin-bottom: 15px;">
            <strong style="color: #008080;">AI Assistant:</strong>
            Hello! How can I assist you with the MedSim platform today?
        </div>
    </div>
    """), unsafe_allow_html=True)

    st.text_input(
        "Type your message here…",
        placeholder="E.g., How do I structure a diagnostic challenge?",
        key="assistant_input"
    )
