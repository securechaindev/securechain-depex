import React, { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import OperationsPage from '../operationsPage/operations'
import GradientCircularProgress from '../components/gradientCircularProgress'
import Box from '@mui/material/Box'
import Collapse from '@mui/material/Collapse'
import IconButton from '@mui/material/IconButton'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Typography from '@mui/material/Typography'
import Paper from '@mui/material/Paper'
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown'
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp'
import TablePagination from '@mui/material/TablePagination'
import Modal from '@mui/material/Modal'

const RepositoriesPage = () => {
  const [owner, set_owner] = useState('')
  const [name, set_name] = useState('')
  const [repositories, set_repositories] = useState([])
  const [page, set_page] = React.useState(0)
  const [rowsPerPage, set_rows_per_page] = React.useState(10)
  const user_id = localStorage.getItem('user_id')

  const on_button_init_click = () => {
    fetch('http://localhost:8000/graph/init', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ owner, name, user_id })
    })
      .then((r) => r.json())
      .then((r) => {
        if ('no_repo' === r.message) {
          window.alert('There is no repository with that owner and name')
        }
        set_owner('')
        set_name('')
      })
  }

  useEffect(() => {
    const intervalId = setInterval(() => {
      fetch('http://localhost:8000/repositories/' + user_id, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
        .then((r) => r.json())
        .then((r) => {
          set_repositories(r)
        })
    }, 10000)

    return () => clearInterval(intervalId)
  })

  const handle_change_page = (newPage) => {
    set_page(newPage)
  }

  const handle_change_rows_per_page = (event) => {
    set_rows_per_page(+event.target.value)
    set_page(0)
  }

  function Row(props) {
    const { repository } = props
    const [open_files, set_open_files] = React.useState(false)
    const [open_modal, set_open_modal] = React.useState(null)

    const handle_open = (name) => set_open_modal(name)
    const handle_close = () => set_open_modal(null)

    return (
      <React.Fragment>
        <TableRow sx={{ '& > *': { borderBottom: 'unset' } }}>
          <TableCell>
            <IconButton aria-label='expand row' size='small' onClick={() => set_open_files(!open_files)}>
              {open_files ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
            </IconButton>
          </TableCell>
          <TableCell align='center'>{repository.owner}</TableCell>
          <TableCell align='center'>{repository.name}</TableCell>
          <TableCell align='center'>
            {repository.is_complete ? <p className='text-gray-600'>Done!</p> : <GradientCircularProgress />}
          </TableCell>
        </TableRow>
        <TableRow>
          <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
            <Collapse in={open_files} timeout='auto' unmountOnExit>
              <Box sx={{ margin: 1 }}>
                <Typography variant='font-bold text-2xl' gutterBottom component='div'>
                  Requirement Files
                </Typography>
                <Table size='small' aria-label='purchases'>
                  <TableHead>
                    <TableRow>
                      <TableCell align='center'>Name</TableCell>
                      <TableCell align='center'>Package Manager</TableCell>
                      <TableCell align='center'>Operations</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {repository.requirement_files.map((requirementFilesRow) => (
                      <TableRow key={requirementFilesRow.name}>
                        <TableCell align='center'>{requirementFilesRow.name}</TableCell>
                        <TableCell align='center'>{requirementFilesRow.manager}</TableCell>
                        <TableCell align='center'>
                          {repository.is_complete ? (
                            <input
                              className='w-44 m-auto justify-center bg-blue-500 hover:bg-blue-700 text-white font-bold text-xs rounded'
                              type='button'
                              onClick={() => handle_open(requirementFilesRow.name)}
                              value={'Reasoning'}
                            />
                          ) : (
                            <p className='text-gray-600'>The repository must be completed</p>
                          )}
                        </TableCell>
                        <Modal
                          open={open_modal === requirementFilesRow.name}
                          onClose={handle_close}
                          aria-labelledby='modal-modal-title'
                          aria-describedby='modal-modal-description'
                          className='relative w-8/12 flex flex-col justify-center m-auto'
                        >
                          <Box className='text-gray-500 text-center border-blue-500 border-2 bg-white rounded-lg shadow'>
                            <Typography id='modal-modal-title' variant='h6' component='h2'>
                              Aply reasoning operations for requirement file {requirementFilesRow.name}
                            </Typography>
                            <OperationsPage
                              id='modal-modal-description'
                              requirement_file_id={requirementFilesRow.requirement_file_id}
                              package_manager={requirementFilesRow.manager}
                            />
                          </Box>
                        </Modal>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Box>
            </Collapse>
          </TableCell>
        </TableRow>
      </React.Fragment>
    )
  }

  return (
    <div className='flex flex-col h-screen justify-center items-center m-auto'>
      <p className='mb-6 text-lg font-normal text-gray-500 lg:text-xl sm:px-16 xl:px-48 dark:text-gray-400 text-center'>
        You must enter here the owner and name of a public repository.
      </p>
      <div className='flex gap-4'>
        <input
          value={owner}
          type='text'
          placeholder='Enter the owner here'
          onKeyDown={(e) => {
            if (e.key === 'Enter') on_button_init_click()
          }}
          onChange={(ev) => set_owner(ev.target.value)}
          className='w-64 shadow appearance-none border rounded w-full py-2 px-2 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline'
        />
        <input
          value={name}
          type='text'
          placeholder='Enter the name here'
          onKeyDown={(e) => {
            if (e.key === 'Enter') on_button_init_click()
          }}
          onChange={(ev) => set_name(ev.target.value)}
          className='w-64 shadow appearance-none border rounded w-full py-2 px-2 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline'
        />
      </div>
      <input
        className='bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded'
        type='button'
        onClick={on_button_init_click}
        value={'Generate'}
      />
      <TableContainer component={Paper}>
        <Table aria-label='collapsible table'>
          <TableHead>
            <TableRow>
              <TableCell />
              <TableCell align='center'>Owner</TableCell>
              <TableCell align='center'>Name</TableCell>
              <TableCell align='center'>Is completed?</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {repositories.map((repository) => (
              <Row key={repository.name} repository={repository} />
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        rowsPerPageOptions={[10, 25, 100]}
        component='div'
        count={repositories.length}
        rowsPerPage={rowsPerPage}
        page={page}
        onPageChange={handle_change_page}
        onRowsPerPageChange={handle_change_rows_per_page}
      />
    </div>
  )
}

RepositoriesPage.propTypes = {
  repository: PropTypes.object
}

export { RepositoriesPage }
