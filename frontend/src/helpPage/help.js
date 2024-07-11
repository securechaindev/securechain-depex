import React from 'react'

const HelpPage = () => {
  return (
    <div className='flex flex-col h-screen justify-center items-center m-auto'>
      <p className='mb-4 text-4xl font-extrabold leading-none tracking-tight text-gray-900 md:text-5xl lg:text-6xl'>Welcome to Depex!</p>
      <p className='mb-6 text-lg font-normal text-gray-500 lg:text-xl sm:px-16 xl:px-48 dark:text-gray-400 text-center'>
        Depex is a tool that allows you to reason over the entire version configuration space of the requirements files of an open-source
        software repository.
      </p>
    </div>
  )
}

export { HelpPage }
