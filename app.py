import streamlit as st
import requests
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================
# CONFIGURATION - Read from Streamlit Secrets or .env
# ============================================================

def get_config():
    """Get configuration from Streamlit Secrets or environment variables"""
    try:
        # Try Streamlit Cloud secrets first
        token = st.secrets["GITHUB_TOKEN"]
        user = st.secrets["GITHUB_USER"]
        repo = st.secrets["GITHUB_REPO"]
        file = st.secrets["GITHUB_FILE"]
    except:
        # Fallback to .env for local development
        token = os.getenv("GITHUB_TOKEN", "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")
        user = os.getenv("GITHUB_USER", "Zedagim2002")
        repo = os.getenv("GITHUB_REPO", "scholarship-tracker")
        file = os.getenv("GITHUB_FILE", "data.json")
    
    return {
        "token": token,
        "user": user,
        "repo": repo,
        "file": file
    }

# ============================================================
# GITHUB OPERATIONS
# ============================================================

def fetch_from_github():
    """Fetch data from GitHub"""
    config = get_config()
    
    url = f"https://api.github.com/repos/{config['user']}/{config['repo']}/contents/{config['file']}"
    
    try:
        response = requests.get(
            url,
            headers={
                'Authorization': f"token {config['token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        
        if response.status_code == 404:
            # Create default file
            default_data = {
                "scholarships": [],
                "jobs": [],
                "masterProfile": {
                    "title": "Maritime GeoAI & Water Resource Engineer",
                    "deadline": ""
                }
            }
            save_to_github(default_data)
            return default_data
        
        if response.status_code != 200:
            st.error(f"GitHub error: {response.status_code}")
            return None
        
        result = response.json()
        content = base64.b64decode(result['content']).decode('utf-8')
        data = json.loads(content)
        
        # Ensure all fields exist
        if 'scholarships' not in data:
            data['scholarships'] = []
        if 'jobs' not in data:
            data['jobs'] = []
        if 'masterProfile' not in data:
            data['masterProfile'] = {
                'title': 'Maritime GeoAI & Water Resource Engineer',
                'deadline': ''
            }
        
        return data
        
    except Exception as e:
        st.error(f"Error fetching from GitHub: {str(e)}")
        return None

def save_to_github(data):
    """Save data to GitHub"""
    config = get_config()
    
    url = f"https://api.github.com/repos/{config['user']}/{config['repo']}/contents/{config['file']}"
    
    # Get current SHA if file exists
    sha = None
    try:
        response = requests.get(
            url,
            headers={
                'Authorization': f"token {config['token']}",
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        if response.status_code == 200:
            sha = response.json()['sha']
    except:
        pass
    
    content = base64.b64encode(
        json.dumps(data, indent=2, default=str).encode('utf-8')
    ).decode('utf-8')
    
    payload = {
        'message': f'Update data - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        'content': content,
        'branch': 'main'
    }
    
    if sha:
        payload['sha'] = sha
    
    try:
        response = requests.put(
            url,
            headers={
                'Authorization': f"token {config['token']}",
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.github.v3+json'
            },
            json=payload
        )
        
        if response.status_code in [200, 201]:
            return True
        else:
            st.error(f"Failed to save: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        st.error(f"Error saving to GitHub: {str(e)}")
        return False

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_days_left(deadline):
    """Calculate days left until deadline"""
    if not deadline:
        return None
    try:
        now = datetime.now().date()
        end = datetime.strptime(deadline, '%Y-%m-%d').date()
        diff = (end - now).days
        return diff
    except:
        return None

def get_status_info(days_left, status):
    """Get status badge info"""
    if status == 'submitted':
        return {'label': '📤 Submitted', 'color': 'gray', 'emoji': '📤'}
    if status == 'accepted':
        return {'label': '✅ Accepted', 'color': 'green', 'emoji': '✅'}
    if status == 'rejected':
        return {'label': '❌ Rejected', 'color': 'red', 'emoji': '❌'}
    
    if days_left is None:
        return {'label': 'No deadline', 'color': 'gray', 'emoji': '📅'}
    if days_left < 0:
        return {'label': f'⏰ Expired ({abs(days_left)} days ago)', 'color': 'red', 'emoji': '⏰'}
    if days_left <= 10:
        return {'label': f'🔴 {days_left} days left', 'color': 'red', 'emoji': '🔴'}
    if days_left <= 20:
        return {'label': f'🟡 {days_left} days left', 'color': 'yellow', 'emoji': '🟡'}
    return {'label': f'🟢 {days_left} days left', 'color': 'green', 'emoji': '🟢'}

# ============================================================
# STREAMLIT UI
# ============================================================

st.set_page_config(
    page_title="🎯 Scholarship & Job Tracker - Ethiopia",
    page_icon="🇪🇹",
    layout="wide"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = {
        'scholarships': [],
        'jobs': [],
        'masterProfile': {
            'title': 'Maritime GeoAI & Water Resource Engineer',
            'deadline': ''
        }
    }

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = 'Dashboard'

# Load data on startup
if st.session_state.get('first_run', True):
    loaded_data = fetch_from_github()
    if loaded_data:
        st.session_state.data = loaded_data
    st.session_state.first_run = False

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/ethiopia.png", width=80)
    st.title("🎯 TrackMaster")
    st.markdown("---")
    
    # Connection status
    config = get_config()
    if config['token'] and config['user']:
        st.success("✅ Connected to GitHub")
    else:
        st.error("❌ GitHub not configured")
    
    st.markdown("---")
    
    # Navigation
    tabs = ["📊 Dashboard", "🎓 Scholarships", "💼 Jobs", "📈 Progress"]
    selected_tab = st.radio("Navigate", tabs, index=tabs.index(st.session_state.current_tab))
    st.session_state.current_tab = selected_tab
    
    st.markdown("---")
    
    # Quick Stats
    st.subheader("📊 Quick Stats")
    total_scholarships = len(st.session_state.data['scholarships'])
    total_jobs = len(st.session_state.data['jobs'])
    active = len([s for s in st.session_state.data['scholarships'] if s.get('status') == 'active']) + \
             len([j for j in st.session_state.data['jobs'] if j.get('status') == 'active'])
    submitted = len([s for s in st.session_state.data['scholarships'] if s.get('status') == 'submitted']) + \
                len([j for j in st.session_state.data['jobs'] if j.get('status') == 'submitted'])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🎓 Scholarships", total_scholarships)
        st.metric("✅ Active", active)
    with col2:
        st.metric("💼 Jobs", total_jobs)
        st.metric("📤 Submitted", submitted)
    
    st.markdown("---")
    st.caption("🇪🇹 Built for Ethiopian scholars")
    st.caption("📦 Data stored on GitHub permanently")

# ============================================================
# DASHBOARD TAB
# ============================================================

if st.session_state.current_tab == "📊 Dashboard":
    st.title("📊 Dashboard")
    
    # Master Profile Section
    st.subheader("👤 Master Profile")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        master_title = st.text_input(
            "Profile Title",
            value=st.session_state.data['masterProfile'].get('title', 'Maritime GeoAI & Water Resource Engineer')
        )
    with col2:
        master_deadline = st.date_input(
            "Target Deadline",
            value=datetime.strptime(st.session_state.data['masterProfile'].get('deadline', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() if st.session_state.data['masterProfile'].get('deadline') else datetime.now().date()
        )
    with col3:
        st.write("")
        st.write("")
        if st.button("💾 Save Profile", type="primary"):
            st.session_state.data['masterProfile']['title'] = master_title
            st.session_state.data['masterProfile']['deadline'] = master_deadline.strftime('%Y-%m-%d')
            if save_to_github(st.session_state.data):
                st.success("✅ Profile saved!")
                st.rerun()
    
    # Stats Cards
    st.markdown("---")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "🎓 Scholarships",
            len(st.session_state.data['scholarships']),
            delta=None
        )
    with col2:
        st.metric(
            "💼 Jobs",
            len(st.session_state.data['jobs']),
            delta=None
        )
    with col3:
        active_count = len([s for s in st.session_state.data['scholarships'] if s.get('status') == 'active']) + \
                      len([j for j in st.session_state.data['jobs'] if j.get('status') == 'active'])
        st.metric(
            "✅ Active",
            active_count,
            delta=None
        )
    with col4:
        urgent = 0
        for s in st.session_state.data['scholarships']:
            days = get_days_left(s.get('deadline'))
            if days is not None and 0 <= days <= 10 and s.get('status') == 'active':
                urgent += 1
        for j in st.session_state.data['jobs']:
            days = get_days_left(j.get('deadline'))
            if days is not None and 0 <= days <= 10 and j.get('status') == 'active':
                urgent += 1
        st.metric(
            "🔴 Urgent",
            urgent,
            delta=None
        )
    with col5:
        submitted_count = len([s for s in st.session_state.data['scholarships'] if s.get('status') == 'submitted']) + \
                         len([j for j in st.session_state.data['jobs'] if j.get('status') == 'submitted'])
        st.metric(
            "📤 Submitted",
            submitted_count,
            delta=None
        )
    
    # Recent Activity
    st.markdown("---")
    st.subheader("📋 Recent Activity")
    
    all_items = []
    for s in st.session_state.data['scholarships']:
        all_items.append({
            'type': '🎓 Scholarship',
            'name': s.get('name', ''),
            'org': s.get('uni', ''),
            'deadline': s.get('deadline', ''),
            'status': s.get('status', 'active'),
            'created': s.get('createdAt', '')
        })
    
    for j in st.session_state.data['jobs']:
        all_items.append({
            'type': '💼 Job',
            'name': j.get('title', ''),
            'org': j.get('company', ''),
            'deadline': j.get('deadline', ''),
            'status': j.get('status', 'active'),
            'created': j.get('createdAt', '')
        })
    
    if all_items:
        df = pd.DataFrame(all_items)
        df = df.sort_values('created', ascending=False).head(10)
        
        for _, row in df.iterrows():
            days = get_days_left(row['deadline'])
            status_info = get_status_info(days, row['status'])
            
            col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
            with col1:
                st.write(row['type'])
            with col2:
                st.write(f"**{row['name']}**")
                st.caption(row['org'])
            with col3:
                st.write(f"📅 {row['deadline'] if row['deadline'] else 'No deadline'}")
                st.caption(status_info['label'])
            with col4:
                if row['status'] == 'active':
                    if st.button(f"📤 Submit", key=f"dash_submit_{row['name']}_{row['created']}"):
                        # Find and update the item
                        if row['type'] == '🎓 Scholarship':
                            for s in st.session_state.data['scholarships']:
                                if s.get('name') == row['name'] and s.get('createdAt') == row['created']:
                                    s['status'] = 'submitted'
                                    break
                        else:
                            for j in st.session_state.data['jobs']:
                                if j.get('title') == row['name'] and j.get('createdAt') == row['created']:
                                    j['status'] = 'submitted'
                                    break
                        if save_to_github(st.session_state.data):
                            st.success("✅ Submitted!")
                            st.rerun()
        st.markdown("---")
    else:
        st.info("No items yet. Start adding scholarships and jobs!")

# ============================================================
# SCHOLARSHIPS TAB
# ============================================================

elif st.session_state.current_tab == "🎓 Scholarships":
    st.title("🎓 Scholarships")
    
    # Add Form
    with st.expander("➕ Add New Scholarship", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            s_name = st.text_input("Scholarship Name *", key="s_name")
            s_uni = st.text_input("University/Organization", key="s_uni")
            s_deadline = st.date_input("Deadline *", key="s_deadline")
            s_country = st.text_input("Country", key="s_country")
        
        with col2:
            s_status = st.selectbox(
                "Status",
                ["active", "submitted", "rejected", "accepted"],
                key="s_status"
            )
            s_funding = st.text_input("Funding (e.g., Full + Living)", key="s_funding")
            s_link = st.text_input("🔗 Application Link", key="s_link")
        
        s_notes = st.text_area("Notes: IELTS, eligibility, documents...", key="s_notes")
        
        if st.button("➕ Add Scholarship", type="primary"):
            if s_name and s_deadline:
                new_scholarship = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S") + "_" + s_name[:10],
                    "name": s_name,
                    "uni": s_uni,
                    "deadline": s_deadline.strftime("%Y-%m-%d"),
                    "status": s_status,
                    "country": s_country,
                    "funding": s_funding,
                    "notes": s_notes,
                    "link": s_link,
                    "createdAt": datetime.now().isoformat()
                }
                st.session_state.data['scholarships'].append(new_scholarship)
                if save_to_github(st.session_state.data):
                    st.success("✅ Scholarship added!")
                    st.rerun()
            else:
                st.error("⚠️ Name and Deadline are required!")
    
    # Display Scholarships
    st.markdown("---")
    
    if st.session_state.data['scholarships']:
        # Filter options
        filter_status = st.selectbox(
            "Filter by status",
            ["All", "active", "submitted", "rejected", "accepted"],
            key="s_filter"
        )
        
        filtered = st.session_state.data['scholarships']
        if filter_status != "All":
            filtered = [s for s in filtered if s.get('status') == filter_status]
        
        # Sort
        filtered = sorted(filtered, key=lambda x: x.get('deadline', '9999-12-31'))
        
        # Display as cards
        for idx, s in enumerate(filtered):
            days = get_days_left(s.get('deadline'))
            status_info = get_status_info(days, s.get('status', 'active'))
            
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{s.get('name', '')}**")
                    st.caption(f"🏛️ {s.get('uni', 'N/A')}")
                    if s.get('country'):
                        st.caption(f"🌍 {s.get('country')}")
                
                with col2:
                    st.write(f"📅 {s.get('deadline', 'No deadline')}")
                    st.write(status_info['label'])
                    if s.get('funding'):
                        st.caption(f"💰 {s.get('funding')}")
                
                with col3:
                    if s.get('notes'):
                        st.caption(f"📝 {s.get('notes')[:100]}...")
                    if s.get('link'):
                        st.caption(f"🔗 [Link]({s.get('link')})")
                
                with col4:
                    if s.get('status') == 'active':
                        if st.button(f"📤 Submit", key=f"s_submit_{idx}_{s.get('id')}"):
                            s['status'] = 'submitted'
                            if save_to_github(st.session_state.data):
                                st.success("✅ Marked as submitted!")
                                st.rerun()
                    if s.get('status') == 'submitted':
                        if st.button(f"↩️ Undo", key=f"s_undo_{idx}_{s.get('id')}"):
                            s['status'] = 'active'
                            if save_to_github(st.session_state.data):
                                st.success("↩️ Undone!")
                                st.rerun()
                    if st.button(f"🗑️ Delete", key=f"s_del_{idx}_{s.get('id')}"):
                        if st.session_state.data['scholarships'].remove(s):
                            if save_to_github(st.session_state.data):
                                st.success("🗑️ Deleted!")
                                st.rerun()
                
                st.markdown("---")
    else:
        st.info("No scholarships added yet. Click 'Add New Scholarship' to get started!")

# ============================================================
# JOBS TAB
# ============================================================

elif st.session_state.current_tab == "💼 Jobs":
    st.title("💼 Jobs")
    
    # Add Form
    with st.expander("➕ Add New Job", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            j_title = st.text_input("Job Title *", key="j_title")
            j_company = st.text_input("Company *", key="j_company")
            j_deadline = st.date_input("Deadline *", key="j_deadline")
            j_location = st.text_input("Location", key="j_location")
        
        with col2:
            j_status = st.selectbox(
                "Status",
                ["active", "submitted", "rejected", "accepted"],
                key="j_status"
            )
            j_salary = st.text_input("Salary (if known)", key="j_salary")
            j_link = st.text_input("🔗 Application Link", key="j_link")
        
        j_notes = st.text_area("Notes: Requirements, skills, contact...", key="j_notes")
        
        if st.button("➕ Add Job", type="primary"):
            if j_title and j_company and j_deadline:
                new_job = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S") + "_" + j_title[:10],
                    "title": j_title,
                    "company": j_company,
                    "deadline": j_deadline.strftime("%Y-%m-%d"),
                    "status": j_status,
                    "location": j_location,
                    "salary": j_salary,
                    "notes": j_notes,
                    "link": j_link,
                    "createdAt": datetime.now().isoformat()
                }
                st.session_state.data['jobs'].append(new_job)
                if save_to_github(st.session_state.data):
                    st.success("✅ Job added!")
                    st.rerun()
            else:
                st.error("⚠️ Title, Company, and Deadline are required!")
    
    # Display Jobs
    st.markdown("---")
    
    if st.session_state.data['jobs']:
        # Filter options
        filter_status = st.selectbox(
            "Filter by status",
            ["All", "active", "submitted", "rejected", "accepted"],
            key="j_filter"
        )
        
        filtered = st.session_state.data['jobs']
        if filter_status != "All":
            filtered = [j for j in filtered if j.get('status') == filter_status]
        
        # Sort
        filtered = sorted(filtered, key=lambda x: x.get('deadline', '9999-12-31'))
        
        # Display as cards
        for idx, j in enumerate(filtered):
            days = get_days_left(j.get('deadline'))
            status_info = get_status_info(days, j.get('status', 'active'))
            
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.markdown(f"**{j.get('title', '')}**")
                    st.caption(f"🏢 {j.get('company', 'N/A')}")
                    if j.get('location'):
                        st.caption(f"📍 {j.get('location')}")
                
                with col2:
                    st.write(f"📅 {j.get('deadline', 'No deadline')}")
                    st.write(status_info['label'])
                    if j.get('salary'):
                        st.caption(f"💰 {j.get('salary')}")
                
                with col3:
                    if j.get('notes'):
                        st.caption(f"📝 {j.get('notes')[:100]}...")
                    if j.get('link'):
                        st.caption(f"🔗 [Link]({j.get('link')})")
                
                with col4:
                    if j.get('status') == 'active':
                        if st.button(f"📤 Submit", key=f"j_submit_{idx}_{j.get('id')}"):
                            j['status'] = 'submitted'
                            if save_to_github(st.session_state.data):
                                st.success("✅ Marked as submitted!")
                                st.rerun()
                    if j.get('status') == 'submitted':
                        if st.button(f"↩️ Undo", key=f"j_undo_{idx}_{j.get('id')}"):
                            j['status'] = 'active'
                            if save_to_github(st.session_state.data):
                                st.success("↩️ Undone!")
                                st.rerun()
                    if st.button(f"🗑️ Delete", key=f"j_del_{idx}_{j.get('id')}"):
                        if st.session_state.data['jobs'].remove(j):
                            if save_to_github(st.session_state.data):
                                st.success("🗑️ Deleted!")
                                st.rerun()
                
                st.markdown("---")
    else:
        st.info("No jobs added yet. Click 'Add New Job' to get started!")

# ============================================================
# PROGRESS TAB
# ============================================================

elif st.session_state.current_tab == "📈 Progress":
    st.title("📈 Progress Overview")
    
    # Combined Graph
    st.subheader("📊 Combined Activity Graph")
    
    # Prepare data for graph
    all_items = []
    for s in st.session_state.data['scholarships']:
        all_items.append({
            'name': s.get('name', 'Unknown'),
            'type': 'Scholarship',
            'deadline': s.get('deadline'),
            'status': s.get('status', 'active'),
            'created': s.get('createdAt', datetime.now().isoformat())
        })
    
    for j in st.session_state.data['jobs']:
        all_items.append({
            'name': j.get('title', 'Unknown'),
            'type': 'Job',
            'deadline': j.get('deadline'),
            'status': j.get('status', 'active'),
            'created': j.get('createdAt', datetime.now().isoformat())
        })
    
    if all_items:
        df = pd.DataFrame(all_items)
        df['days_left'] = df['deadline'].apply(lambda x: get_days_left(x) if x else None)
        df['created_date'] = pd.to_datetime(df['created']).dt.date
        
        # Create color mapping
        def get_color(row):
            if row['status'] == 'submitted':
                return 'gray'
            days = row['days_left']
            if days is None:
                return 'blue'
            if days < 0:
                return 'red'
            if days <= 10:
                return 'red'
            if days <= 20:
                return 'yellow'
            return 'green'
        
        df['color'] = df.apply(get_color, axis=1)
        
        # Create bubble chart
        fig = go.Figure()
        
        # Scholarships
        s_df = df[df['type'] == 'Scholarship']
        if not s_df.empty:
            fig.add_trace(go.Scatter(
                x=s_df['created_date'],
                y=s_df['days_left'],
                mode='markers+text',
                name='🎓 Scholarships',
                text=s_df['name'],
                textposition="top center",
                marker=dict(
                    size=20,
                    color=s_df['color'].map({'green': '#4caf50', 'yellow': '#ffc107', 'red': '#e94560', 'gray': '#999', 'blue': '#2d6a9f'}),
                    opacity=0.7
                ),
                hovertemplate='<b>%{text}</b><br>Days Left: %{y}<br>Created: %{x}<extra></extra>'
            ))
        
        # Jobs
        j_df = df[df['type'] == 'Job']
        if not j_df.empty:
            fig.add_trace(go.Scatter(
                x=j_df['created_date'],
                y=j_df['days_left'],
                mode='markers+text',
                name='💼 Jobs',
                text=j_df['name'],
                textposition="top center",
                marker=dict(
                    size=20,
                    color=j_df['color'].map({'green': '#4caf50', 'yellow': '#ffc107', 'red': '#e94560', 'gray': '#999', 'blue': '#2d6a9f'}),
                    opacity=0.7,
                    symbol='diamond'
                ),
                hovertemplate='<b>%{text}</b><br>Days Left: %{y}<br>Created: %{x}<extra></extra>'
            ))
        
        fig.update_layout(
            title='📈 Application Timeline & Deadlines',
            xaxis_title='Date Created',
            yaxis_title='Days Left Until Deadline',
            height=500,
            hovermode='closest',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # Add horizontal lines for zones
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.3, annotation_text="🟢 Safe Zone")
        fig.add_hline(y=20, line_dash="dash", line_color="yellow", opacity=0.3, annotation_text="🟡 Warning Zone")
        fig.add_hline(y=10, line_dash="dash", line_color="red", opacity=0.3, annotation_text="🔴 Urgent Zone")
        fig.add_hline(y=0, line_dash="solid", line_color="red", opacity=0.5)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics
        st.subheader("📊 Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🎓 Scholarships")
            if st.session_state.data['scholarships']:
                s_status = pd.DataFrame(st.session_state.data['scholarships'])['status'].value_counts()
                for status, count in s_status.items():
                    st.write(f"- {status}: {count}")
            else:
                st.write("No scholarships")
        
        with col2:
            st.markdown("### 💼 Jobs")
            if st.session_state.data['jobs']:
                j_status = pd.DataFrame(st.session_state.data['jobs'])['status'].value_counts()
                for status, count in j_status.items():
                    st.write(f"- {status}: {count}")
            else:
                st.write("No jobs")
        
        with col3:
            st.markdown("### ⚡ Summary")
            total = len(st.session_state.data['scholarships']) + len(st.session_state.data['jobs'])
            active = len([s for s in st.session_state.data['scholarships'] if s.get('status') == 'active']) + \
                    len([j for j in st.session_state.data['jobs'] if j.get('status') == 'active'])
            submitted = len([s for s in st.session_state.data['scholarships'] if s.get('status') == 'submitted']) + \
                       len([j for j in st.session_state.data['jobs'] if j.get('status') == 'submitted'])
            st.write(f"- Total: {total}")
            st.write(f"- Active: {active}")
            st.write(f"- Submitted: {submitted}")
            if total > 0:
                st.write(f"- Completion: {submitted/total*100:.1f}%")
    else:
        st.info("No data yet. Start adding scholarships and jobs to see progress!")

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.caption("🇪🇹 Built for Ethiopian scholars & professionals | All data stored permanently on GitHub | 🇪🇹 Fully Funded only")
