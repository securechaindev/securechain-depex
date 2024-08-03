import React from 'react'
import { Link } from 'react-router-dom'

const PageNotFound = () => {
  return (
    <div className='flex flex-col h-screen justify-center items-center m-auto'>
      <p className='mb-4 text-4xl font-extrabold leading-none tracking-tight text-gray-900 md:text-5xl lg:text-9xl'>ERROR 404</p>
      <p className='mb-6 text-lg font-normal text-gray-500 lg:text-xl sm:px-16 xl:px-48 dark:text-gray-400 text-center'>
        I&apos;s look like you&apos;re lost...
      </p>
      <p style={{ textAlign: 'center' }}>
        <Link className='bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded' to='/'>
          Go to Home
        </Link>
      </p>
    </div>
  )
}

export default PageNotFound
