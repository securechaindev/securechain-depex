import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import PropTypes from 'prop-types'

const AuthContext = createContext()

const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('acess_token'))

  useEffect(() => {
    if (token) {
      localStorage.setItem('acess_token', token)
    } else {
      localStorage.removeItem('acess_token')
    }
  }, [token])

  const contextValue = useMemo(
    () => ({
      token,
      setToken
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
