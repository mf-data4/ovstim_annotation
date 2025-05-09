import streamlit as st
import pandas as pd
import io

# Load the data
df = pd.read_csv("data/example_table.csv")
df.columns = df.columns.str.strip()

# Ask for nurse name at start
if 'nurse_name' not in st.session_state:
    st.session_state.nurse_name = ""

if not st.session_state.nurse_name:
    nurse_name = st.text_input("Please enter your name to begin annotating:", "")
    if nurse_name.strip():
        st.session_state.nurse_name = nurse_name.strip()
        st.rerun()
    else:
        st.stop()

# Get unique patients
unique_patients = df['Patient'].unique().tolist()

# Session state init
if 'patient_index' not in st.session_state:
    st.session_state.patient_index = 0
if 'day_index' not in st.session_state:
    st.session_state.day_index = 0
if 'summaries' not in st.session_state:
    st.session_state.summaries = {}
if 'ready_to_continue' not in st.session_state:
    st.session_state.ready_to_continue = False

# Stop if all patients are complete
if st.session_state.patient_index >= len(unique_patients):
    st.success("All patients have been reviewed!")
    st.stop()

# Current patient
patient = unique_patients[st.session_state.patient_index]
patient_df = df[df['Patient'] == patient].copy()
patient_df['Cycle Day'] = patient_df['Cycle Day'].astype(int)
patient_df.sort_values('Cycle Day', inplace=True)
days = patient_df['Cycle Day'].tolist()

# Set current day
day_index = st.session_state.day_index
current_day = days[day_index]

st.title("Ovarian Stimulation Cycle Annotation Tool")
st.header(f"👤 {patient} – Cycle Day {current_day}")

# Show patient-level info
patient_info = patient_df.iloc[0]
st.markdown(f"""
**Protocol:** {patient_info['Protocol']}  
**Cycle Notes:** {patient_info['Cycle Notes']}  
**AMH:** {patient_info['AMH']}
""")

# Show all days up to current
for _, row in patient_df[patient_df['Cycle Day'] <= current_day].iterrows():
    day = row['Cycle Day']
    st.subheader(f"🗓️ Cycle Day {day}")
    st.markdown(f"""
    - **E2:** {row['E2']}
    - **P4:** {row['P4']}
    - **Left Ovary Follicles:** {row['Left Ovary Follicles']}
    - **Right Ovary Follicles:** {row['Right Ovary Follicles']}
    - **Medication Instructions:** {row['Medication Instructions']}
    - **Clinician Instruction:** {row['Clinician Instruction']}
    """)
    if day in st.session_state.summaries:
        st.info(f"📝 **Saved Summary:**\n\n{st.session_state.summaries[day]}")

# Summary input
existing = st.session_state.summaries.get(current_day, "")
summary = st.text_area("Add a concise description (3-4 sentences) of what these measurements mean for the patient and how they should be interpreting it. Essentially this would replace some of the guidance/education you'd normally give patients during monitoring updates:", value=existing, key=f"summary_day_{current_day}")

# Navigation buttons
col1, col2, col3 = st.columns([1, 1, 4])

# Previous
with col1:
    if st.button("⬅️ Previous Cycle Day", disabled=day_index == 0):
        st.session_state.day_index = max(0, day_index - 1)
        st.rerun()

# Final day logic
if day_index == len(days) - 1:
    with col2:
        if st.button("💾 Save and Prepare Download"):
            if not summary.strip():
                st.error("❌ Please enter a summary for the final day before saving.")
                st.stop()

            # Save final summary
            st.session_state.summaries[current_day] = summary.strip()

            # Prepare annotated CSV
            annotated_df = patient_df.copy()
            annotated_df['Summary'] = annotated_df['Cycle Day'].apply(
                lambda day: st.session_state.summaries.get(day, "")
            )

            buffer = io.StringIO()
            annotated_df.to_csv(buffer, index=False)
            buffer.seek(0)
            st.session_state.csv_string = buffer.getvalue()

            nurse_clean = st.session_state.nurse_name.replace(" ", "_")
            st.session_state.filename = f"annotated_{patient.replace(' ', '_')}_nurse_{nurse_clean}.csv"

            st.session_state.ready_to_continue = True

    # Show download if ready
    if st.session_state.ready_to_continue:
        st.success("✅ Final summary saved. Click below to download.")
        st.download_button(
            label=f"📥 Download CSV for {patient}",
            data=st.session_state.csv_string,
            file_name=st.session_state.filename,
            mime="text/csv"
        )
        # if st.button("➡️ Continue to Next Patient"):
        #     st.session_state.patient_index += 1
        #     st.session_state.day_index = 0
        #     st.session_state.summaries = {}
        #     st.session_state.ready_to_continue = False
        #     st.rerun()
else:
    with col2:
        if st.button("➡️ Next Cycle Day"):
            if not summary.strip():
                st.error("❌ Please enter a summary before moving to the next day.")
            else:
                st.session_state.summaries[current_day] = summary.strip()
                st.session_state.day_index = min(len(days) - 1, day_index + 1)
                st.rerun()

# # Restart current patient
# if st.button("🔁 Start Over for This Patient"):
#     st.session_state.day_index = 0
#     st.session_state.summaries = {}
#     st.session_state.ready_to_continue = False
#     st.warning("Patient restarted from Day 1.")
#     st.rerun()

# Redo/Skip controls
col_redo, col_skip = st.columns([1, 1])

with col_skip:
    if st.button("⏭️ Next Patient"):
        st.session_state.patient_index += 1
        st.session_state.day_index = 0
        st.session_state.summaries = {}
        st.session_state.ready_to_continue = False
        st.info("Moving to next patient.")
        st.rerun()

with col_redo:
    if st.button("⏮️ Redo Previous Patient", disabled=st.session_state.patient_index == 0):
        st.session_state.patient_index = max(0, st.session_state.patient_index - 1)
        st.session_state.day_index = 0
        st.session_state.summaries = {}
        st.session_state.ready_to_continue = False
        st.rerun()
