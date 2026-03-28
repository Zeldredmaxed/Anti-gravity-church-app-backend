import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { DashboardView } from './pages/DashboardView';
import { MembersView } from './pages/MembersView';
import { GivingView } from './pages/GivingView';
import { AttendanceView } from './pages/AttendanceView';
import { EventsView } from './pages/EventsView';
import { GroupsView } from './pages/GroupsView';
import { CareView } from './pages/CareView';
import { VolunteersView } from './pages/VolunteersView';
import { SettingsView } from './pages/SettingsView';
import { ProfileView } from './pages/ProfileView';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardView />} />
          <Route path="people" element={<MembersView />} />
          <Route path="giving" element={<GivingView />} />
          <Route path="attendance" element={<AttendanceView />} />
          <Route path="events" element={<EventsView />} />
          <Route path="groups" element={<GroupsView />} />
          <Route path="care" element={<CareView />} />
          <Route path="volunteers" element={<VolunteersView />} />
          <Route path="settings" element={<SettingsView />} />
          <Route path="profile" element={<ProfileView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
