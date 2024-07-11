import React from 'react'
import PropTypes from 'prop-types'
import FormControl from '@mui/material/FormControl'
import InputLabel from '@mui/material/InputLabel'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'

const AgregatorSelect = ({ agregator, set_agregator }) => {
  const handle_agregator_change = (event) => {
    set_agregator(event.target.value)
  }

  return (
    <FormControl sx={{ m: 1, minWidth: 150 }} size='small'>
      <InputLabel>Agregator</InputLabel>
      <Select value={agregator} label='Agregator' onChange={handle_agregator_change}>
        <MenuItem value={'mean'}>Mean</MenuItem>
        <MenuItem value={'weighted_mean'}>Weighted Mean</MenuItem>
      </Select>
    </FormControl>
  )
}

AgregatorSelect.propTypes = {
  agregator: PropTypes.string,
  set_agregator: PropTypes.func
}

export default AgregatorSelect
