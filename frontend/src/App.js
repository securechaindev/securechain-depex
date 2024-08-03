import React from 'react'
import { AuthProvider } from './auth/authProvider'

import Routes from './routes/routes'

function App() {
  return (
    <div className='flex'>
      <AuthProvider>
        <Routes />
      </AuthProvider>
    </div>
  )
}

export default App
