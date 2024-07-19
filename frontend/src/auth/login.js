import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { EyeIcon, EyeOffIcon } from 'lucide-react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Modal from '@mui/material/Modal'

const LoginPage = () => {
  const [email, set_email] = useState('')
  const [password, set_password] = useState('')
  const [email_error, set_email_error] = useState('')
  const [password_error, set_password_error] = useState('')

  const navigate = useNavigate()

  const on_button_login_click = () => {
    set_email_error('')
    set_password_error('')

    if ('' === email) {
      set_email_error('Please enter your email')
      return
    }

    if (!/^[\w-\\.]+@([\w-]+\.)+[\w-]{2,4}$/.test(email)) {
      set_email_error('Please enter a valid email')
      return
    }

    if ('' === password) {
      set_password_error('Please enter a password')
      return
    }

    log_in()
  }

  const log_in = () => {
    fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    })
      .then((r) => r.json())
      .then((r) => {
        if ('success' === r.message) {
          localStorage.setItem('access_token', r.access_token)
          localStorage.setItem('user_id', r.user_id)
          navigate('/')
          window.location.reload()
        } else if ('user_no_exist' === r.message) {
          handle_open()
        } else {
          window.alert('Wrong email or password')
        }
      })
  }

  const [passValue, setPassValue] = useState({
    showPassword: false
  })

  const handle_click_show_password = () => {
    setPassValue({ ...passValue, showPassword: !passValue.showPassword })
  }

  const [open, set_open] = React.useState(false)
  const handle_open = () => set_open(true)
  const handle_close = () => set_open(false)

  const on_button_register_click = () => {
    navigate('/signup')
  }

  return (
    <div className='flex flex-wrap flex-col h-screen justify-center items-center m-auto'>
      <p className='mb-4 text-4xl font-extrabold leading-none tracking-tight text-gray-900 md:text-5xl lg:text-6xl'>Login</p>
      <br />
      <div className='relative inline-flex'>
        <input
          value={email}
          type='text'
          placeholder='Enter your email here'
          onKeyDown={(e) => {
            if (e.key === 'Enter') on_button_login_click()
          }}
          onChange={(ev) => set_email(ev.target.value)}
          className='w-64 shadow appearance-none border rounded w-full py-2 px-2 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline'
        />
      </div>
      <div className='relative inline-flex'>
        <input
          value={password}
          type={passValue.showPassword ? 'text' : 'password'}
          placeholder='Enter your password here'
          onKeyDown={(e) => {
            if (e.key === 'Enter') on_button_login_click()
          }}
          onChange={(ev) => set_password(ev.target.value)}
          className='w-64 shadow appearance-none border rounded w-full py-2 px-2 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline'
        />
        <div className='absolute end-2 top-2' onClick={handle_click_show_password}>
          {passValue.showPassword ? <EyeIcon /> : <EyeOffIcon />}
        </div>
      </div>
      <label className='text-red-600'>{email_error}</label>
      <label className='text-red-600'>{password_error}</label>
      <input
        className='bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded'
        type='button'
        onClick={on_button_login_click}
        value={'Log in'}
      />
      <div className='space-x-1 flex'>
        <p className='text-gray-500 text-xs'>If you haven&quot;t an account you can </p>{' '}
        <p className='underline text-gray-500 text-xs' onClick={on_button_register_click}>
          register
        </p>
      </div>
      <Modal
        open={open}
        onClose={handle_close}
        aria-labelledby='modal-modal-title'
        aria-describedby='modal-modal-description'
        className='relative max-w-96 flex flex-col justify-center m-auto'
      >
        <Box className='text-gray-500 text-center border-blue-500 border-2 bg-white rounded-lg shadow'>
          <Typography id='modal-modal-title' variant='h6' component='h2'>
            Email not registered
          </Typography>
          <Typography id='modal-modal-description' sx={{ mt: 2 }}>
            An account does not exist with this email address: {email}. Do you want to create a new account?
          </Typography>
          <input
            className='bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded'
            type='button'
            onClick={on_button_register_click}
            value={'Sign up'}
          />
        </Box>
      </Modal>
    </div>
  )
}

export { LoginPage }
