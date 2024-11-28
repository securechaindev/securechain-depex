import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { EyeIcon, EyeOffIcon } from 'lucide-react'
import Button from '@mui/material/Button'

const SignUpPage = () => {
  const [email, set_email] = useState('')
  const [password, set_password] = useState('')
  const [repeated_password, set_repeated_password] = useState('')
  const [email_error, set_email_error] = useState('')
  const [password_error, set_password_error] = useState('')
  const [repeated_password_error, set_repeated_password_error] = useState('')

  const navigate = useNavigate()

  const on_button_sign_up_click = () => {
    set_email_error('')
    set_password_error('')
    set_repeated_password_error('')

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

    if (password != repeated_password) {
      set_repeated_password_error('The password must be the same')
      return
    }

    if (!/^(?=.*[A-Z])(?=.*\d)(?=.*[\W_])[A-Za-z\d\W_]{8,20}$/.test(password)) {
      set_password_error(
        'The password must have between 8 and 20 characters, contain at least one capital letter, one number and one special character'
      )
      return
    }

    sign_up()
  }

  const sign_up = () => {
    fetch('http://localhost:8000/auth/signup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email, password })
    })
      .then((r) => r.json())
      .then((r) => {
        if ('success' === r.message) {
          navigate('/login')
        } else if ('user_already_exists' == r.message) {
          window.alert('User already exist')
        }
      })
  }

  const [passValue, setPassValue] = useState({
    showPassword: false
  })

  const [repeatedPassValue, setRepeatedPassValue] = useState({
    showRepeatedPassword: false
  })

  const handleClickShowPassword = () => {
    setPassValue({ ...passValue, showPassword: !passValue.showPassword })
  }

  const handleClickShowRepeatedPassword = () => {
    setRepeatedPassValue({ ...repeatedPassValue, showRepeatedPassword: !repeatedPassValue.showRepeatedPassword })
  }

  return (
    <div className='flex flex-wrap flex-col h-screen justify-center items-center m-auto space-y-2'>
      <p className='mb-4 text-4xl font-extrabold leading-none tracking-tight text-gray-900 md:text-5xl lg:text-6xl'>Sign Up</p>
      <div className='relative inline-flex'>
        <input
          value={email}
          type='text'
          placeholder='Enter your email here'
          onKeyDown={(e) => {
            if (e.key === 'Enter') on_button_sign_up_click()
          }}
          onChange={(ev) => set_email(ev.target.value)}
          className='w-64 shadow appearance-none border rounded py-2 px-2 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline'
        />
      </div>
      <div className='relative inline-flex'>
        <input
          value={password}
          type={passValue.showPassword ? 'text' : 'password'}
          onKeyDown={(e) => {
            if (e.key === 'Enter') on_button_sign_up_click()
          }}
          placeholder='Enter your password here'
          onChange={(ev) => set_password(ev.target.value)}
          className='w-64 shadow appearance-none border rounded py-2 px-2 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline'
        />
        <div className='absolute end-2 top-2' onClick={handleClickShowPassword}>
          {passValue.showPassword ? <EyeIcon /> : <EyeOffIcon />}
        </div>
      </div>
      <div className='relative inline-flex'>
        <input
          value={repeated_password}
          type={repeatedPassValue.showRepeatedPassword ? 'text' : 'password'}
          onKeyDown={(e) => {
            if (e.key === 'Enter') on_button_sign_up_click()
          }}
          placeholder='Confirm your password here'
          onChange={(ev) => set_repeated_password(ev.target.value)}
          className='w-64 shadow appearance-none border rounded py-2 px-2 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline'
        />
        <div className='absolute end-2 top-2' onClick={handleClickShowRepeatedPassword}>
          {repeatedPassValue.showRepeatedPassword ? <EyeIcon /> : <EyeOffIcon />}
        </div>
      </div>
      <label className={`text-red-600 ${email_error !== '' ? '' : 'hidden'}`}>{email_error}</label>
      <label className={`text-red-600 ${password_error !== '' ? '' : 'hidden'}`}>{password_error}</label>
      <label className={`text-red-600 ${repeated_password_error !== '' ? '' : 'hidden'}`}>{repeated_password_error}</label>
      <Button variant="contained" onClick={on_button_sign_up_click}>Sign Up</Button>
    </div>
  )
}

export { SignUpPage }
