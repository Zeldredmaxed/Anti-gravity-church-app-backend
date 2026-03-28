# Newbirth Anti-Gravity Church App - Admin Dashboard Features Prompt

*Copy and paste the text below into your AI website builder (Lovable, Cursor, Bolt.new, v0, etc.).*

***

## System Role & Objective
Act as an expert frontend engineer, specializing in React, Vite, TypeScript, Tailwind CSS, and shadcn-ui. Please build a comprehensive, ultra-premium Admin Dashboard single-page application (SPA) for the "Newbirth Anti-Gravity Church App". 

## Design & Aesthetics (CRITICAL)
- **Ultra-Premium UI**: The dashboard needs to look like a top-tier modern SAAS (e.g., Vercel, Stripe, Linear). 
- **Aesthetic**: Use a highly polished design system. Incorporate dark/light mode functionality (defaulting to a sleek dark theme or a highly refined light theme with subtle gray backgrounds).
- **Details**: Use glassmorphism where appropriate, smooth transitions (`transition-all duration-300`), soft shadows, and vibrant accent colors (e.g., deep purples, golds, or ocean blues depending on the brand context). 
- **Components**: Do not use generic, plain tables. Use beautifully crafted data grids, metric cards with micro-animations on hover, and modern typography (Inter, Outfit, or Roboto).

## Tech Stack
- **Framework**: React (via Vite App)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui, Radix UI primitives
- **Icons**: Lucide React
- **Routing**: React Router DOM v6
- **State/Data Fetching**: React Query (or standard hooks/context for UI state)
- **Charts**: Recharts

## Layout Structure
1. **Sidebar Navigation**: Collapsible sidebar containing links to all modules, a user profile dropdown at the bottom, and a master "Settings" gear.
2. **Top Header**: Global search bar, notifications bell, breadcrumbs, and a primary call-to-action (e.g., "Quick Add").
3. **Main Content Area**: Scrollable content pane where all the individual pages render.

## Core Pages & Features Required

### 1. Overview Dashboard (Home)
- **Metric Cards**: Total Members, Weekly Giving, Weekend Attendance, New Visitors.
- **Activity Feed**: A timeline or activity list showing recent events (e.g., "John Doe checked into Youth Group", "New donation of $500 received").
- **Charts**: A line chart displaying attendance trends over the last 6 months, and a bar chart showing giving totals.

### 2. People / Directory (Members & Families)
- **Members Table**: A rich datatable showing Name, Email, Phone, Membership Status (Active, Visitor, etc.), and Last Visited date. Features needed: search, filtering, and pagination.
- **Member Profile View**: A detailed slide-out panel or page showing a specific member's info, their giving history, attendance history, family members, and notes.
- **Families**: Ability to group members into households.

### 3. Giving & Donations
- **Summary Cards**: Total YTD giving, Monthly recurring total.
- **Transactions List**: Table showing recent donations with columns for Donor, Amount, Fund (e.g., Tithes, Missions), Date, and Status.
- **Funds Management**: Simple cards showing the health of different funds.
- *Note for AI*: Render a placeholder view for connecting a Stripe account for payment gateway processing.

### 4. Events & Check-ins
- **Calendar View**: A monthly/weekly calendar displaying upcoming services and events.
- **Event Details**: Config for an event (Time, Location, Description).
- **Check-ins**: A specific view allowing scanning (mocked) or manual entry for member attendance. 

### 5. Communications
- **Broadcast Hub**: An interface to compose and send mass SMS or Emails to specific groups (e.g., "Send SMS to all Youth Group parents").
- Message templates support and preview panel.
- Sent History log with mock open rates.

### 6. Small Groups & Ministries
- Grid view of active groups (e.g., Men's Ministry, Youth Group, Connect Group).
- Detail view showing Group Leader, meeting times, and roster of members.

### 7. Social & Media (Sermons, Posts, Glory Clips)
- **Sermons**: A media manager to upload/edit sermon metadata (Title, Series, Speaker, Date, Video Link).
- **Glory Clips**: Short-form video moderation dashboard. Mock video cards showing "Amen" counts and Comment counts.
- **Community Posts**: A feed of community announcements requiring admin approval/moderation.

### 8. Automations (Workflows)
- A Kanban or list interface showing "If This Then That" church rules. 
- Examples: "If 1st Time Visitor -> Then Send Welcome SMS", "If Missed 3 Sundays -> Then Alert Pastor".

### 9. AI Assistant
- A floating or dedicated chat window where the admin can "talk to their data." (e.g., "Who hasn't given this month?"). Just the UI interface with a chat input and message bubbles.

## General Instructions
- Generate realistic mock data for all tables and charts so the application feels alive and immediately testable.
- Ensure all forms (like "Add Member", "Create Event", "Compose Email") have validation UI states and beautiful modal/dialog dialogs, even if they don't actually post to a backend yet.
- Optimize for a fully responsive layout (mobile, tablet, desktop).
- Setup routing so a user can click through the entire application without refreshing the page.
