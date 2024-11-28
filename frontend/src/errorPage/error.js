import React from 'react'
import { useNavigate } from 'react-router-dom'
import Button from '@mui/material/Button'

const PageNotFound = () => {
  const navigate = useNavigate()

  const on_click_navigate_home = () => {
    navigate('/')
  }

  return (
    <div className='flex flex-col h-screen justify-center items-center m-auto'>
      <p className='mb-4 text-4xl font-extrabold leading-none tracking-tight text-gray-900 md:text-5xl lg:text-9xl'>ERROR 404</p>
      <p className='mb-6 text-lg font-normal text-gray-500 lg:text-xl sm:px-16 xl:px-48 dark:text-gray-400 text-center'>
        I&apos;s look like you&apos;re lost...
      </p>
      <Button variant="contained" onClick={() => on_click_navigate_home()}>Go to Home</Button>
    </div>
  )
}

export default PageNotFound
