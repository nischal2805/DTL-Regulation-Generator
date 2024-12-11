import streamlit as st
import pandas as pd
import sqlite3
import requests
import json
import datetime

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect("data__1.db")
    cursor = conn.cursor()
    # Create tables if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age INTEGER,
            gender TEXT,
            knows_autonomous TEXT,
            timestamp TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question TEXT,
            response TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    # Create posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')

    # Create comments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            user_id INTEGER,
            parent_comment_id INTEGER,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES posts(id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(parent_comment_id) REFERENCES comments(id)
        )
    ''')

    conn.commit()
    conn.close()

# Insert user details into the database
def insert_user(name, age, gender, knows_autonomous):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO users (name, age, gender, knows_autonomous, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (name, age, gender, knows_autonomous, timestamp))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

# Insert responses into the database
def insert_responses(user_id, responses):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    for question, response in responses.items():
        cursor.execute("""
            INSERT INTO responses (user_id, question, response)
            VALUES (?, ?, ?)
        """, (user_id, question, response))
    conn.commit()
    conn.close()

# Fetch data for regulation generation
def fetch_data():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM responses")
    responses = cursor.fetchall()
    conn.close()
    return users, responses

# Functions to handle posts and comments
def insert_post(user_id, content):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO posts (user_id, content) VALUES (?, ?)", (user_id, content))
    conn.commit()
    conn.close()

def insert_comment(post_id, user_id, content, parent_comment_id=None):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO comments (post_id, user_id, content, parent_comment_id) VALUES (?, ?, ?, ?)",
        (post_id, user_id, content, parent_comment_id)
    )
    conn.commit()
    conn.close()

def get_posts():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT posts.id, users.name, posts.content, posts.created_at
        FROM posts
        JOIN users ON posts.user_id = users.id
        ORDER BY posts.created_at DESC
    """)
    posts = cursor.fetchall()
    conn.close()
    return posts

def get_comments(post_id):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT comments.id, comments.post_id, comments.user_id, comments.content, comments.created_at,
               comments.parent_comment_id, users.name
        FROM comments
        JOIN users ON comments.user_id = users.id
        WHERE comments.post_id = ?
        ORDER BY comments.created_at ASC
    """, (post_id,))
    comments = cursor.fetchall()
    conn.close()
    return comments

# Function to fetch all responses for batch processing
def fetch_all_responses():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT responses FROM user_responses")
    data = cursor.fetchall()
    conn.close()
    all_responses = [json.loads(res[0]) for res in data]
    return all_responses

# Function to process responses in batches
def batch_process_responses():
    all_responses = fetch_all_responses()
    batch_size = 10  # Adjust batch size as needed for efficiency
    for i in range(0, len(all_responses), batch_size):
        batch = all_responses[i:i+batch_size]
        # Prepare the prompt for Llama API
        prompt = prepare_prompt(batch)
        # Call the Llama API with the batch prompt
        regulation = generate_regulation(prompt)
        # Handle the regulation as needed

def generate_regulation(prompt):
    llama_endpoint = "http://127.0.0.1:11434/api/generate"

    payload = {
        "model": "llama3.1",
        "prompt": prompt,
        "temperature": 0.7,
        "max_tokens": 512,
        # Include any other parameters required by the API
    }

    try:
        response = requests.post(llama_endpoint, json=payload)
        if response.status_code == 200:
            # Handle streaming or non-streaming responses appropriately
            result = response.json()
            generated_text = result.get('response', '')
            return generated_text
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred: {e}")
        return None

def prepare_prompt(responses_batch):
    prompt = "Based on the following responses, generate ethical guidelines for autonomous vehicles:\n\n"
    for user_num, user_responses in enumerate(responses_batch, 1):
        prompt += f"User {user_num} Responses:\n"
        for q_num, answer in user_responses.items():
            question = questions[int(q_num[1:]) - 1]["question"]
            prompt += f"{question}\nAnswer: {answer}\n\n"
    return prompt

# Llama API endpoint
llama_endpoint = "http://127.0.0.1:11434/api/generate"

# Initialize database
init_db()

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Go to", ["Home", "User Details", "Questionnaire", "Forum", "Regulation Generator", "Download Data"])


# 1. Home Page
if page == "Home":
    st.title("Welcome to the Autonomous Vehicles Ethics App")
    st.write("""
        This app collects user opinions on ethical considerations for autonomous vehicles.
        Your DATA is being used for generation of regulations for ai makers to give guidelines to developers.
        Please proceed through the pages to provide your input.
        Answer All the Questions Carefully and then feel free to chat on our forum page and interact with other users.
             








             Created BY:
                Nischal R E(1RV23CS157)
                Niranjan R N(1RV23CS156)
                Pavan V(1RV23CS165)
    """)

# 2. User Details Page
elif page == "User Details":
    st.title("Your Details")
    st.subheader("Please provide your information:")

    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])
    knows_autonomous = st.selectbox("Do you know about autonomous vehicles?", ["Yes", "No"])

    if st.button("Submit"):
        if name.strip():
            user_id = insert_user(name.strip(), age, gender, knows_autonomous)
            st.session_state['user_id'] = user_id
            st.success("Information saved!")
        else:
            st.error("Name cannot be empty.")

# 3. Questionnaire Page
elif page == "Questionnaire":
    st.title("Ethical Questionnaire")

    questions = [
        {
            "question": "Should autonomous vehicles prioritize saving passengers over pedestrians, or should every life be treated equally?",
            "input_type": "selectbox",
            "options": ["Prioritize Passengers", "Treat Every Life Equally", "Prioritize Pedestrians"]
        },
        {
            "question": "In a situation where only one life can be saved, should age (e.g., child vs. elderly) influence the decision?",
            "input_type": "selectbox",
            "options": ["Yes, prioritize the younger", "No, every life is equal", "Not Sure"]
        },
        {
            "question": "How should autonomous vehicles handle situations involving animals on the road? Should they prioritize human safety over animal lives?",
            "input_type": "text_area"
        },
        {
            "question": "Would you feel comfortable knowing an autonomous vehicle might sacrifice your safety to save a larger group of people?",
            "input_type": "radio",
            "options": ["Yes", "No", "Maybe"]
        },
        {
            "question": "What ethical principles should guide the decisions of autonomous vehicles during accidents?",
            "input_type": "text_area"
        },
        {
            "question": "Should autonomous vehicles be programmed to follow traffic rules strictly, even if it means a higher risk of accidents?",
            "input_type": "radio",
            "options": ["Yes", "No", "Depends on the situation"]
        },
        {
            "question": "How much control should humans retain over autonomous vehicles during emergencies?",
            "input_type": "slider",
            "min": 0,
            "max": 100,
            "step": 10,
            "format": "%d%%"
        },
        {
            "question": "Should autonomous vehicles always favor minimizing overall harm, even if it means choosing the 'lesser evil'?",
            "input_type": "radio",
            "options": ["Yes", "No", "Not Sure"]
        },
        {
            "question": "Should AVs consider environmental factors (e.g., swerving into a tree vs. hitting a pedestrian) in their decision-making process?",
            "input_type": "radio",
            "options": ["Yes", "No", "Depends on Context"]
        },
        {
            "question": "Do you think AVs should prioritize the safety of pedestrians over bicyclists or motorcyclists? Why or why not?",
            "input_type": "text_area"
        },
        {
            "question": "How much do you trust autonomous vehicles to make ethical decisions during accidents?",
            "input_type": "slider",
            "min": 0,
            "max": 100,
            "step": 10,
            "format": "%d%%"
        },
        {
            "question": "Are you aware of any laws or guidelines that regulate the ethical behavior of autonomous vehicles?",
            "input_type": "radio",
            "options": ["Yes", "No", "Not Sure"]
        },
        {
            "question": "How do you feel about autonomous vehicles sharing your personal data (e.g., location, driving habits) with governments or companies?",
            "input_type": "text_area"
        },
        {
            "question": "What would make you feel more confident in adopting autonomous vehicle technology?",
            "input_type": "text_area"
        },
        {
            "question": "Are you aware of any cases where an autonomous vehicle was involved in an ethical dilemma or accident?",
            "input_type": "text_input"
        },
        {
            "question": "What concerns you most about the rise of autonomous vehicles (e.g., safety, job loss, hacking)?",
            "input_type": "text_area"
        },
        {
            "question": "Do you worry that autonomous vehicles might make biased decisions based on the data they are trained on?",
            "input_type": "radio",
            "options": ["Yes", "No", "Somewhat"]
        },
        {
            "question": "What role should government and policymakers play in ensuring AVs make ethical decisions?",
            "input_type": "text_area"
        },
        {
            "question": "Do you think manufacturers should be held legally responsible for accidents caused by autonomous vehicles? Why or why not?",
            "input_type": "text_area"
        },
        {
            "question": "Would you trust autonomous vehicles in extreme weather conditions (e.g., heavy rain, snow, fog)? Why or why not?",
            "input_type": "text_area"
        },
        {
            "question": "How do you think autonomous vehicles could impact community safety in crowded urban areas?",
            "input_type": "text_area"
        },
        {
            "question": "What role should AVs play in public transportation systems to ensure inclusivity for everyone?",
            "input_type": "text_area"
        },
        {
            "question": "Do you think autonomous vehicles could help reduce discrimination in law enforcement (e.g., fewer biased stops)?",
            "input_type": "radio",
            "options": ["Yes", "No", "Maybe"]
        },
        {
            "question": "How should AVs interact with vulnerable groups like people with disabilities, children, or the elderly in public spaces?",
            "input_type": "text_area"
        },
        {
            "question": "What cultural differences do you think might influence how countries program their autonomous vehicles?",
            "input_type": "text_area"
        },
        {
            "question": "How would society change if autonomous vehicles became the primary mode of transportation?",
            "input_type": "text_area"
        },
        {
            "question": "In a future dominated by AVs, should human-driven cars be banned for safety reasons?",
            "input_type": "radio",
            "options": ["Yes", "No", "Not Sure"]
        },
        {
            "question": "What potential benefits could AVs bring to developing countries where infrastructure is less advanced?",
            "input_type": "text_area"
        },
        {
            "question": "Do you think AVs will lead to the end of traffic accidents altogether, or will they introduce new risks?",
            "input_type": "text_area"
        },
        {
            "question": "Could AVs evolve to prioritize not just individual safety but environmental sustainability (e.g., avoiding pollution hotspots)?",
            "input_type": "text_area"
        },
        {
            "question": "Would you feel comfortable letting a car drive you without any human intervention? Why or why not?",
            "input_type": "text_area"
        },
        {
            "question": "Do you believe autonomous vehicles could reduce stress or anxiety for drivers and passengers?",
            "input_type": "radio",
            "options": ["Yes", "No", "Maybe"]
        },
        {
            "question": "How would you cope with the idea that an AV might prioritize someone else’s life over yours in an emergency?",
            "input_type": "text_area"
        },
        {
            "question": "Do you trust machines to make moral decisions better than humans? Why or why not?",
            "input_type": "text_area"
        },
        {
            "question": "If you were in an AV during a critical decision moment, would you prefer to be aware of what the car is doing or be left in the dark?",
            "input_type": "radio",
            "options": ["Prefer to be aware", "Prefer not to know", "Not Sure"]
        },
        {
            "question": "Do you believe AVs should have free will to make decisions or strictly follow human-programmed rules?",
            "input_type": "selectbox",
            "options": ["Have Free Will", "Follow Human Rules", "Combination of Both"]
        },
        {
            "question": "What does it mean for a machine to act ethically, and can machines truly understand morality?",
            "input_type": "text_area"
        },
        {
            "question": "If an AV had to choose between saving two equally valued lives, should it act randomly or rely on a predefined rule?",
            "input_type": "selectbox",
            "options": ["Act Randomly", "Use Predefined Rule", "Not Sure"]
        },
        {
            "question": "Should AVs be programmed with regional ethics (e.g., Western vs. Eastern values), or should there be universal standards?",
            "input_type": "selectbox",
            "options": ["Regional Ethics", "Universal Standards", "Not Sure"]
        },
        {
            "question": "Is it ethical to make decisions about life and death using algorithms, or should humans always have the final say?",
            "input_type": "text_area"
        },
        {
            "question": "How do you think AVs will impact jobs in driving industries (e.g., truck drivers, taxi drivers)?",
            "input_type": "text_area"
        },
        {
            "question": "Would you pay more for an AV that allows you to customize its ethical decision-making (e.g., prioritize family safety)?",
            "input_type": "radio",
            "options": ["Yes", "No", "Maybe"]
        },
        {
            "question": "Do you think AVs will make transportation cheaper or more expensive in the long run?",
            "input_type": "selectbox",
            "options": ["Cheaper", "More Expensive", "Stay the Same"]
        },
        {
            "question": "How should insurance policies adapt to cover accidents involving autonomous vehicles?",
            "input_type": "text_area"
        },
        {
            "question": "Who should pay for damages caused by AV malfunctions—the manufacturer, the owner, or the software provider?",
            "input_type": "selectbox",
            "options": ["Manufacturer", "Owner", "Software Provider", "Shared Responsibility"]
        }
    ]

    responses = {}

    for idx, item in enumerate(questions, 1):
        question = item["question"]
        input_type = item["input_type"]

        st.write(f"**{idx}. {question}**")

        if input_type == "radio":
            response = st.radio("", item["options"], key=f"q{idx}")
        elif input_type == "selectbox":
            response = st.selectbox("", item["options"], key=f"q{idx}")
        elif input_type == "slider":
            response = st.slider(
                "", min_value=item["min"], max_value=item["max"], step=item["step"],
                format=item.get("format", "%d"), key=f"q{idx}"
            )
        elif input_type == "text_area":
            response = st.text_area("", key=f"q{idx}")
        elif input_type == "text_input":
            response = st.text_input("", key=f"q{idx}")
        else:
            response = None
            st.error("Unknown input type.")
        responses[f"Q{idx}"] = response
        st.write("---")

    if st.button("Submit Answers"):
        if 'user_id' in st.session_state:
            # Insert responses into the database
            insert_responses(st.session_state['user_id'], responses)
            st.success("Responses saved!")
        else:
            st.error("Please submit your details first.")

# 4. Forum Page
elif page == "Forum":
    st.title("Community Forum")
    st.subheader("Interact with other users!")

    if 'user_id' in st.session_state:
        st.write("### Create a New Post")
        new_post = st.text_area("What's on your mind?", key="new_post")
        if st.button("Post", key="post_button"):
            if new_post.strip():
                insert_post(st.session_state['user_id'], new_post.strip())
                st.success("Post created!")
                st.experimental_rerun()  # Refresh the page to show the new post
            else:
                st.error("Post content cannot be empty.")
    else:
        st.warning("Please submit your details on the User Details page to post.")

    st.write("---")
    st.write("### Recent Posts")
    posts = get_posts()
    if posts:
        for post in posts:
            post_id, author_name, post_content, post_created_at = post
            st.markdown(f"**{author_name}** posted at {post_created_at}")
            st.write(post_content)

            # Display comments
            comments = get_comments(post_id)

            # Function to display comments recursively
            def display_comments(comments_list, parent_id=None, level=0):
                for comment in comments_list:
                    comment_id = comment[0]
                    comment_post_id = comment[1]
                    comment_user_id = comment[2]
                    comment_content = comment[3]
                    comment_created_at = comment[4]
                    comment_parent_id = comment[5]
                    commenter_name = comment[6]

                    if comment_parent_id == parent_id:
                        indent = "&nbsp;" * 4 * level
                        st.markdown(f"{indent}**{commenter_name}** replied at {comment_created_at}")
                        st.markdown(f"{indent}{comment_content}")

                        # Reply to comment
                        if 'user_id' in st.session_state:
                            with st.expander(f"{indent}Reply", expanded=False):
                                reply_content = st.text_area(f"Reply to {commenter_name}", key=f"reply_{comment_id}")
                                if st.button(f"Submit Reply to Comment {comment_id}", key=f"submit_reply_{comment_id}"):
                                    if reply_content.strip():
                                        insert_comment(post_id, st.session_state['user_id'], reply_content.strip(), parent_comment_id=comment_id)
                                        st.success("Reply added!")
                                        st.experimental_rerun()  # Refresh to show the new reply
                                    else:
                                        st.error("Reply cannot be empty.")
                        # Recursive call to display nested comments
                        display_comments(comments_list, parent_id=comment_id, level=level+1)

            display_comments(comments)

            # Add a comment to the post
            if 'user_id' in st.session_state:
                st.write("**Add a comment:**")
                comment_content = st.text_input(f"Your comment on post {post_id}", key=f"comment_{post_id}")
                if st.button(f"Submit Comment to Post {post_id}", key=f"submit_comment_{post_id}"):
                    if comment_content.strip():
                        insert_comment(post_id, st.session_state['user_id'], comment_content.strip())
                        st.success("Comment added!")
                        st.experimental_rerun()  # Refresh to show the new comment
                    else:
                        st.error("Comment cannot be empty.")
            else:
                st.warning("Please submit your details to comment.")

            st.write("---")
    else:
        st.write("No posts yet. Be the first to post!")

# 5. Regulation Generator Page
elif page == "Regulation Generator":
    st.title("Generate Ethical Guidelines")
    st.subheader("Aggregated user data is used to create actionable AI regulations.")
    users, responses = fetch_data()
    
    if users and responses:
        # Prepare prompt for the model
        prompt = "Based on the following inputs:\n"
        for user in users:
            prompt += f"- User: {user}\n"
        for response in responses:
            prompt += f"- Response: {response}\n"
        prompt += "Generate ethical regulations for autonomous vehicles."
        
        # Send prompt to Llama API
        with st.spinner("Generating regulations..."):
            try:
                response = requests.post(llama_endpoint, json={
                    "model": "llama3.1:latest",
                    "prompt": prompt,
                    "max_tokens": 200
                }, stream=True)  # Use stream=True to handle chunked responses

                if response.status_code == 200:
                    # Stream response handling
                    regulations = ""
                    for chunk in response.iter_lines():
                        if chunk:
                            try:
                                # Parse JSON lines
                                data = json.loads(chunk.decode('utf-8'))
                                regulations += data.get("response", "")
                            except json.JSONDecodeError as e:
                                st.error(f"JSON decode error: {e}")
                    
                    if regulations:
                        st.success("Regulations generated successfully!")
                        st.write("### Generated Regulations:")
                        st.write(regulations)
                        
                        if st.button("Save Regulations"):
                            with open("regulations.txt", "w") as file:
                                file.write(regulations)
                            st.success("Regulations saved as 'regulations.txt'!")
                    else:
                        st.error("No regulations were generated. Check the API or input data.")
                else:
                    st.error(f"Failed to connect to the Llama API: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {e}")
    else:
        st.warning("Not enough data to generate regulations. Complete previous steps.")
