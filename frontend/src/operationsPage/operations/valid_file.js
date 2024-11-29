import React, { useState } from 'react'
import PropTypes from 'prop-types'

const ValidFileOperation = (props) => {
  const access_token = useState(localStorage.getItem('access_token'))[0]
  const { requirement_file_id, package_manager, set_operation_result } = props
  const [_max_level, set_max_level] = useState('')

  const [max_level_error, set_max_level_error] = useState('')

  const on_button_valid_operation = () => {
    set_max_level_error('')

    if (_max_level < 1 && _max_level != -1) {
      set_max_level_error('The max level must be greater than 0 or equal -1')
      return
    }

    const max_level = _max_level != -1 ? _max_level * 2 : _max_level

    fetch('http://localhost:8000/operation/file/valid_file', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${access_token}`
      },
      body: JSON.stringify({ requirement_file_id, max_level, package_manager })
    })
      .then((r) => r.json())
      .then((r) => {
        if ('success' === r.message) {
          if (r.is_valid) {
            set_operation_result({ result: 'The file is Valid' })
          } else {
            set_operation_result({ result: 'The file is not Valid' })
          }
        } else if ('no_dependencies' === r.message) {
          window.alert("The requirement file don't have dependencies")
        }
      })
  }

  return (
    <div className='flex-col flex'>
      <p>Valid File Operation</p>
      <input
        value={_max_level}
        type='number'
        min='-1'
        placeholder='Enter the max level here'
        onKeyDown={(e) => {
          if (e.key === 'Enter') on_button_valid_operation()
        }}
        onChange={(ev) => set_max_level(ev.target.value)}
        className='w-64 shadow appearance-none border rounded w-full py-2 px-2 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline'
      />
      <label className='text-red-600'>{max_level_error}</label>
      <input
        className='bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded'
        type='button'
        onClick={on_button_valid_operation}
        value={'Apply'}
      />
    </div>
  )
}

ValidFileOperation.propTypes = {
  requirement_file_id: PropTypes.string,
  package_manager: PropTypes.string,
  set_operation_result: PropTypes.func
}

export default ValidFileOperation
