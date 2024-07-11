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
  const [owner, setOwner] = useState('')
  const [name, setName] = useState('')
  const [repositories, setRepositories] = useState([])
  const [page, setPage] = React.useState(0)
  const [rowsPerPage, setRowsPerPage] = React.useState(10)
  const user_id = localStorage.getItem('user_id')

  const onButtonInitClick = () => {
    fetch('http://localhost:8000/graph/init', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ owner, name, user_id })
    })
    window.location.reload()
  }

  useEffect(() => {
    fetch('http://localhost:8000/repositories/' + user_id, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
      .then((r) => r.json())
      .then((r) => {
        setRepositories(r)
      })
  }, [])

  const handleChangePage = (newPage) => {
    setPage(newPage)
  }

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(+event.target.value)
    setPage(0)
  }

  function Row(props) {
    const { repository } = props
    const [openFiles, setOpenFiles] = React.useState(false)
    const [openModal, setOpenModal] = React.useState(null)

    const handleOpen = (name) => setOpenModal(name)
    const handleClose = () => setOpenModal(null)

    return (
      <React.Fragment>
        <TableRow sx={{ '& > *': { borderBottom: 'unset' } }}>
          <TableCell>
            <IconButton aria-label='expand row' size='small' onClick={() => setOpenFiles(!openFiles)}>
              {openFiles ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
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
            <Collapse in={openFiles} timeout='auto' unmountOnExit>
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
                              onClick={() => handleOpen(requirementFilesRow.name)}
                              value={'Reasoning'}
                            />
                          ) : (
                            <p className='text-gray-600'>The repository must be completed</p>
                          )}
                        </TableCell>
                        <Modal
                          open={openModal === requirementFilesRow.name}
                          onClose={handleClose}
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
          onChange={(ev) => setOwner(ev.target.value)}
          className='w-64 shadow appearance-none border rounded w-full py-2 px-2 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline'
        />
        <input
          value={name}
          type='text'
          placeholder='Enter the name here'
          onChange={(ev) => setName(ev.target.value)}
          className='w-64 shadow appearance-none border rounded w-full py-2 px-2 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline'
        />
      </div>
      <input
        className='bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded'
        type='button'
        onClick={onButtonInitClick}
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
        onPageChange={handleChangePage}
        onRowsPerPageChange={handleChangeRowsPerPage}
      />
    </div>
  )
}

RepositoriesPage.propTypes = {
  repository: PropTypes.object
}

export { RepositoriesPage }
