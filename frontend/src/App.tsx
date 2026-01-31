import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import TestExplorer from './pages/TestExplorer';
import TestRunner from './pages/TestRunner';
import ResultPage from './pages/ResultPage';
import HistoryPage from './pages/HistoryPage';
import SettingsPage from './pages/SettingsPage';
import Pipeline from './pages/Pipeline';
import ApiDocs from './pages/ApiDocs';
import Changelog from './pages/Changelog';

import UserProfile from './pages/UserProfile';
import LoginPage from './pages/LoginPage';
import { ProtectedRoute } from './contexts/AuthContext';

function App() {
  return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        
        <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route index element={<Home />} />
          <Route path="tests" element={<TestExplorer />} />
          <Route path="test/:testId" element={<TestRunner />} />
          <Route path="result/:resultId" element={<ResultPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="profile" element={<UserProfile />} />
          <Route path="api-docs" element={<ApiDocs />} />
          <Route path="changelog" element={<Changelog />} />
          
          <Route path="pipeline" element={
            <ProtectedRoute adminOnly>
              <Pipeline />
            </ProtectedRoute>
          } />
          <Route path="settings" element={
            <ProtectedRoute adminOnly>
              <SettingsPage />
            </ProtectedRoute>
          } />
        </Route>
      </Routes>
  );
}

export default App;
