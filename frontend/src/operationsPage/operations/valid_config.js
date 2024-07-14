import React, { useState } from 'react'
import PropTypes from 'prop-types'
import AgregatorSelect from '../utils/agregator'

const ValidConfigOperation = (props) => {
  const { requirement_file_id, package_manager, set_operation_result } = props
  const [_max_level, set_max_level] = useState('')
  const [agregator, set_agregator] = useState('mean')
  const [text_config, set_text_config] = useState('')
  const [config, set_config] = useState('')

  const [max_level_error, set_max_level_error] = useState('')
  const [configError, set_config_error] = useState('')

  const have_string_values_only = (obj) => {
    if (typeof obj !== 'object' || obj === null) {
      return false
    }
    for (const key in obj) {
      if (typeof obj[key] !== 'string') {
        return false
      }
    }
    return true
  }

  const on_button_valid_config_operation = () => {
    set_max_level_error('')
    set_config_error('')

    if (_max_level < 1 && _max_level != -1) {
      set_max_level_error('The max level must be greater than 0 or equal -1')
      return
    }

    try {
      set_config(JSON.parse(text_config))
      if (!have_string_values_only(config)) {
        set_config_error('JSON should only contain string values')
        return
      }
    } catch (error) {
      set_config_error('Invalid JSON')
      return
    }

    const max_level = _max_level != -1 ? _max_level * 2 : _max_level

    fetch('http://localhost:8000/operation/config/valid_config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ requirement_file_id, max_level, package_manager, agregator, config })
    })
      .then((r) => r.json())
      .then((r) => {
        if ('success' === r.message) {
          set_operation_result(r)
        } else if ('no_dependencies' === r.message) {
          window.alert("The requirement file don't have dependencies")
        }
      })
  }

  return (
    <div className='flex-col flex'>
      <p>Valid Config Operation</p>
      <input
        value={_max_level}
        type='number'
        min='-1'
        placeholder='Enter the max level here'
        onKeyDown={(e) => {
          if (e.key === 'Enter') on_button_valid_config_operation()
        }}
        onChange={(ev) => set_max_level(ev.target.value)}
        className='w-64 shadow appearance-none border rounded w-full py-2 px-2 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline'
      />
      <label className='text-red-600'>{max_level_error}</label>
      <textarea
        value={text_config}
        rows='10'
        cols='50'
        placeholder='Enter a config of versions here'
        onKeyDown={(e) => {
          if (e.key === 'Enter') on_button_valid_config_operation()
        }}
        onChange={(ev) => set_text_config(ev.target.value)}
        className='border-2'
      />
      <label className='text-red-600'>{configError}</label>
      <AgregatorSelect agregator={agregator} set_agregator={set_agregator} />
      <input
        className='bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded'
        type='button'
        onClick={on_button_valid_config_operation}
        value={'Apply'}
      />
    </div>
  )
}

ValidConfigOperation.propTypes = {
  requirement_file_id: PropTypes.string,
  package_manager: PropTypes.string,
  set_operation_result: PropTypes.func
}

export default ValidConfigOperation
