import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import PropTypes from 'prop-types'

const AuthContext = createContext()

const AuthProvider = ({ children }) => {
  const [token, set_token] = useState(localStorage.getItem('access_token'))

  useEffect(() => {
    if (token) {
      localStorage.setItem('access_token', token)
    } else {
      localStorage.removeItem('access_token')
    }
  }, [token])

  const contextValue = useMemo(
    () => ({
      token,
      set_token
    }),
    [token]
  )

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
}

function useAuth() {
  return useContext(AuthContext)
}

AuthProvider.propTypes = {
  children: PropTypes.object
}

export { useAuth, AuthProvider }

export default AuthProvider
