import React, { useState } from 'react'
import PropTypes from 'prop-types'
import InputLabel from '@mui/material/InputLabel'
import MenuItem from '@mui/material/MenuItem'
import FormControl from '@mui/material/FormControl'
import Select from '@mui/material/Select'
import ValidFileOperation from './operations/valid_file'
import MinimiseImpactOperation from './operations/minimise_impact'
import MaximiseImpactOperation from './operations/maximise_impact'
import FilterConfigsOperation from './operations/filter_configs'
import ValidConfigOperation from './operations/valid_config'
import CompleteConfigOperation from './operations/complete_config'
import ConfigByImpactOperation from './operations/config_by_impact'

export default function OperationsPage(props) {
  const { requirement_file_id, package_manager } = props
  const [operation, set_operation] = useState('')
  const [operation_result, set_operation_result] = useState(null)

  const handle_operation_change = (event) => {
    set_operation(event.target.value)
  }

  const select_operation = () => {
    if (operation === 'valid_file') {
      return (
        <ValidFileOperation
          requirement_file_id={requirement_file_id}
          package_manager={package_manager}
          set_operation_result={set_operation_result}
        />
      )
    } else if (operation === 'minimise') {
      return (
        <MinimiseImpactOperation
          requirement_file_id={requirement_file_id}
          package_manager={package_manager}
          set_operation_result={set_operation_result}
        />
      )
    } else if (operation === 'maximise') {
      return (
        <MaximiseImpactOperation
          requirement_file_id={requirement_file_id}
          package_manager={package_manager}
          set_operation_result={set_operation_result}
        />
      )
    } else if (operation === 'filter') {
      return (
        <FilterConfigsOperation
          requirement_file_id={requirement_file_id}
          package_manager={package_manager}
          set_operation_result={set_operation_result}
        />
      )
    } else if (operation === 'valid_config') {
      return (
        <ValidConfigOperation
          requirement_file_id={requirement_file_id}
          package_manager={package_manager}
          set_operation_result={set_operation_result}
        />
      )
    } else if (operation === 'complete') {
      return (
        <CompleteConfigOperation
          requirement_file_id={requirement_file_id}
          package_manager={package_manager}
          set_operation_result={set_operation_result}
        />
      )
    } else if (operation === 'config_by_impact') {
      return (
        <ConfigByImpactOperation
          requirement_file_id={requirement_file_id}
          package_manager={package_manager}
          set_operation_result={set_operation_result}
        />
      )
    } else {
      return
    }
  }

  return (
    <div className='flex-col flex justify-center items-center'>
      <FormControl sx={{ m: 1, minWidth: 150 }} size='small'>
        <InputLabel>Operation</InputLabel>
        <Select value={operation} label='Operation' onChange={handle_operation_change}>
          <MenuItem value=''>
            <em>None</em>
          </MenuItem>
          <MenuItem value={'valid_file'}>Valid File</MenuItem>
          <MenuItem value={'minimise'}>Minimise Impact</MenuItem>
          <MenuItem value={'maximise'}>Maximise Impact</MenuItem>
          <MenuItem value={'filter'}>Filter Configs</MenuItem>
          <MenuItem value={'valid_config'}>Valid Config</MenuItem>
          <MenuItem value={'complete'}>Complete Config</MenuItem>
          <MenuItem value={'config_by_impact'}>Config By Impact</MenuItem>
        </Select>
      </FormControl>
      {select_operation()}
      {operation_result ? (
        <pre className='border-2 text-left max-h-72 overflow-y-auto border-gray-300 text-left whitespace-pre-wrap p-4'>
          {JSON.stringify(operation_result.result, null, 2)}
        </pre>
      ) : null}
      <br />
    </div>
  )
}

OperationsPage.propTypes = {
  requirement_file_id: PropTypes.string,
  package_manager: PropTypes.string
}
