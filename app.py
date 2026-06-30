import streamlit as st
import pandas as pd

# পেজ কনফিগারেশন সেটআপ
st.set_page_config(page_title="MCT Read & Test App", page_icon="❓", layout="centered")

st.title("❓ MCT Read & Test App")

# প্রয়োজনীয় কলামের নাম (Case-sensitive)
REQUIRED_COLUMNS = [
    "subjectcode",
    "questiontext",
    "option1",
    "option2",
    "option3",
    "option4",
    "answer",
    "questionlevel"
]

# সেশন স্টেট (Session State) ইনিশিয়ালাইজেশন
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# --- ১. ফাইল আপলোড সেকশন ---
with st.expander("📁 Upload Questions", expanded=st.session_state.quiz_data is None):
    st.markdown("""
    ### Upload Excel File (.xlsx)
    দয়া করে একটি এক্সেল ফাইল (`.xlsx`) আপলোড করুন যাতে আপনার কুইজের প্রশ্নগুলো রয়েছে। নিশ্চিত করুন যে আপনার শিটের প্রথম সারিতে নিচের কলাম হেডারগুলো হুবহু (case-sensitive) রয়েছে:
    * **subjectcode**: প্রশ্নের বিষয় বা টপিক (যেমন, "Aerodynamics")
    * **questiontext**: সম্পূর্ণ প্রশ্নটি
    * **option1, option2, option3, option4**: চারটি সম্ভাব্য উত্তরের অপশন
    * **answer**: সঠিক অপশনের নম্বরটি (যেমন, option1-এর জন্য `1`, option2-এর জন্য `2`, ইত্যাদি)
    * **questionlevel**: প্রশ্নের कठिनতার স্তর (যেমন, "Easy", "Moderate", "Difficult")
    * **questiongroup**: (ঐচ্ছিক/Optional) প্রশ্নের গ্রুপ বা ক্যাটাগরি (যেমন, Armt-1, Armt-2)
    """)
    
    uploaded_file = st.file_uploader("Choose File", type=["xlsx"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            # কলামগুলো যাচাই করা
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            
            if missing_cols:
                st.error(f"❌ প্রয়োজনীয় এই কলামগুলো ফাইলে পাওয়া যায়নি: {', '.join(missing_cols)}")
            else:
                st.success("✅ ফাইলটি সফলভাবে আপলোড এবং যাচাই করা হয়েছে!")
                st.session_state.quiz_data = df
                st.session_state.user_answers = {}
                st.session_state.submitted = False
        except Exception as e:
            st.error(f"ফাইল রিড করতে সমস্যা হয়েছে: {e}")

# --- ২. মূল অ্যাপ্লিকেশন ফ্লো ---
if st.session_state.quiz_data is not None:
    df = st.session_state.quiz_data
    
    # সাইডবার ফিল্টার (Sidebar Filters)
    st.sidebar.header("🎯 Filters")
    
    # ১. সাবজেক্ট ফিল্টার
    subjects = ["All"] + list(df["subjectcode"].dropna().unique())
    selected_subject = st.sidebar.selectbox("Select Subject", subjects)
    
    # ২. নতুন গ্রুপ ফিল্টার (Armt-1, Armt-2, Armt-3 এর জন্য)
    if "questiongroup" in df.columns:
        groups = ["All"] + list(df["questiongroup"].dropna().unique())
        selected_group = st.sidebar.selectbox("Select Question Group", groups)
    else:
        selected_group = "All"
    
    # ৩. ডিফিকাল্টি লেভেল ফিল্টার
    levels = ["All"] + list(df["questionlevel"].dropna().unique())
    selected_level = st.sidebar.selectbox("Select Difficulty Level", levels)
    
    # ফিল্টার অনুযায়ী ডাটা আলাদা করা
    filtered_df = df.copy()
    if selected_subject != "All":
        filtered_df = filtered_df[filtered_df["subjectcode"] == selected_subject]
    if selected_group != "All" and "questiongroup" in df.columns:
        filtered_df = filtered_df[filtered_df["questiongroup"] == selected_group]
    if selected_level != "All":
        filtered_df = filtered_df[filtered_df["questionlevel"] == selected_level]
        
    # মোড সিলেকশন (Mode Selection)
    mode = st.radio("Select Mode:", ["📖 Read Mode", "📝 Test Mode"], horizontal=True)
    
    st.markdown("---")
    
    if filtered_df.empty:
        st.warning("নির্ধারিত ফিল্টার অনুযায়ী কোনো প্রশ্ন পাওয়া যায়নি। অন্য ফিল্টার সিলেক্ট করে দেখুন।")
        
    elif mode == "📖 Read Mode":
        st.subheader(f"Reviewing {len(filtered_df)} Questions")
        
        for idx, row in filtered_df.iterrows():
            with st.container(border=True):
                # হেডার ইনফো
                group_info = f" | Group: {row['questiongroup']}" if 'questiongroup' in row and pd.notna(row['questiongroup']) else ""
                st.caption(f"Subject: {row['subjectcode']} | Level: {row['questionlevel']}{group_info}")
                
                # প্রশ্ন
                st.markdown(f"**Q: {row['questiontext']}**")
                
                # অপশনসমূহ
                st.write(f"1️⃣ {row['option1']}")
                st.write(f"2️⃣ {row['option2']}")
                st.write(f"3️⃣ {row['option3']}")
                st.write(f"4️⃣ {row['option4']}")
                
                # সঠিক উত্তর চেক (Error হ্যান্ডেল সহ)
                try:
                    correct_ans_num = int(row['answer'])
                    correct_text = row[f'option{correct_ans_num}']
                    st.markdown(f"👉 **Correct Answer:** Option {correct_ans_num} — *{correct_text}*")
                except:
                    st.error(f"❌ এই প্রশ্নের 'answer' কলামের ডাটাতে সমস্যা আছে। ফাইলে ১, ২, ৩ অথবা ৪ দেওয়া আছে কিনা চেক করুন।")

    elif mode == "📝 Test Mode":
        st.subheader(f"Quiz Panel ({len(filtered_df)} Questions)")
        
        # কুইজ ফর্ম
        with st.form(key="quiz_form"):
            for idx, row in filtered_df.iterrows():
                st.markdown(f"**Q: {row['questiontext']}**")
                
                options = [
                    f"1. {row['option1']}",
                    f"2. {row['option2']}",
                    f"3. {row['option3']}",
                    f"4. {row['option4']}"
                ]
                
                saved_ans = st.session_state.user_answers.get(idx, None)
                default_idx = options.index(saved_ans) if saved_ans in options else None
                
                choice = st.radio(
                    f"Choose one option for question {idx}",
                    options,
                    index=default_idx,
                    key=f"q_{idx}",
                    label_visibility="collapsed"
                )
                st.session_state.user_answers[idx] = choice
                st.markdown("---")
                
            submit_button = st.form_submit_button(label="Submit Test")
            
        if submit_button or st.session_state.submitted:
            st.session_state.submitted = True
            score = 0
            total = len(filtered_df)
            
            st.subheader("📊 Test Results")
            
            for idx, row in filtered_df.iterrows():
                user_choice = st.session_state.user_answers.get(idx)
                
                with st.container(border=True):
                    st.markdown(f"**Question:** {row['questiontext']}")
                    
                    try:
                        correct_num = int(row['answer'])
                        correct_text = f"{correct_num}. {row[f'option{correct_num}']}"
                        
                        if user_choice == correct_text:
                            st.success(f"✅ Correct! You chose: {user_choice}")
                            score += 1
                        else:
                            st.error(f"❌ Incorrect. You chose: {user_choice if user_choice else 'No answer selected'}")
                            st.info(f"💡 Correct Answer: {correct_text}")
                    except:
                        st.error("❌ এই প্রশ্নের 'answer' কলামের সঠিক উত্তরটি রিড করা যায়নি।")
            
            # স্কোর সামারি কার্ড
            percentage = (score / total) * 100 if total > 0 else 0
            st.metric(label="Your Total Score", value=f"{score} / {total}", delta=f"{percentage:.1f}%")
            
            if percentage >= 80:
                st.balloons()
