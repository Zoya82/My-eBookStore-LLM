import HomePage from './pages/HomePage'
import AdminPortal from './pages/AdminPortal'
import './App.css'
import { AuthProvider } from './auth/AuthContext'

function App() {
  const isAdminPath = window.location.pathname === '/admin' || window.location.pathname === '/admin/'
  return <AuthProvider>{isAdminPath ? <AdminPortal /> : <HomePage />}</AuthProvider>
}

export default App
