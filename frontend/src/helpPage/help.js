import React from 'react'
import Accordion from '@mui/material/Accordion'
import AccordionSummary from '@mui/material/AccordionSummary'
import AccordionDetails from '@mui/material/AccordionDetails'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'

const HelpPage = () => {
  const [expanded, setExpanded] = React.useState(false)

  const handleChange = (panel) => (event, isExpanded) => {
    setExpanded(isExpanded ? panel : false)
  }

  return (
    <div className='flex flex-col h-screen justify-center m-auto pr-36 pl-36'>
      <p className='mb-4 text-4xl font-extrabold leading-none tracking-tight text-gray-900 md:text-5xl lg:text-6xl'>
        Frequently Asked Questions
      </p>
      <Accordion expanded={expanded === 'panel1'} onChange={handleChange('panel1')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>How to use Valid File Operation?</AccordionSummary>
        <AccordionDetails>
          The Valid File Operation checks if a file is valid up to a specified maximum depth level, if you want to check up to the last
          level you must enter -1.
        </AccordionDetails>
      </Accordion>
      <Accordion expanded={expanded === 'panel2'} onChange={handleChange('panel2')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>How to use Minimise Impact Operation?</AccordionSummary>
        <AccordionDetails>
          The Mimise Impact Operation returns version configurations with the closest impact to zero. You must indicate the desired depth
          level, the limit of configurations to return and the impact aggregator you want to use.
        </AccordionDetails>
      </Accordion>
      <Accordion expanded={expanded === 'panel3'} onChange={handleChange('panel3')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>How to use Maximise Operation?</AccordionSummary>
        <AccordionDetails>
          The Maximise Impact Operation returns version configurations with the closest impact to ten. You must indicate the desired depth
          level, the limit of configurations to return and the impact aggregator you want to use.
        </AccordionDetails>
      </Accordion>
      <Accordion expanded={expanded === 'panel4'} onChange={handleChange('panel4')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>How to use Filter Configs Operation?</AccordionSummary>
        <AccordionDetails>
          The Filter Configs Operation returns version configurations between a maximun impact and a minimun impact. You must indicate the
          desired depth level, the limit of configurations to return, the impact aggregator you want to use, the maximun impact and the
          minimun impact.
        </AccordionDetails>
      </Accordion>
      <Accordion expanded={expanded === 'panel5'} onChange={handleChange('panel5')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>How to use Valid Config Operation?</AccordionSummary>
        <AccordionDetails>
          The Valid Config Operation returns if a configuration of versions is valid for a file. You must indicate the desired depth level,
          the impact aggregator you want to use and the configuration in json format.
        </AccordionDetails>
      </Accordion>
      <Accordion expanded={expanded === 'panel6'} onChange={handleChange('panel6')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>How to use Complete Config Operation?</AccordionSummary>
        <AccordionDetails>
          The Complete Config Operation returns if a complete configuration with the closest impact to zero from a partial configuration.
          You must indicate the desired depth level, the impact aggregator you want to use and the partial configuration in json format.
        </AccordionDetails>
      </Accordion>
      <Accordion expanded={expanded === 'panel7'} onChange={handleChange('panel7')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>How to use Config By Impact Operation?</AccordionSummary>
        <AccordionDetails>
          The Config By Impact Operation returns the configuration closest to a given impact. You must indicate the desired depth level, the
          impact aggregator you want to use and the impact.
        </AccordionDetails>
      </Accordion>
      <Accordion expanded={expanded === 'panel8'} onChange={handleChange('panel8')}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>What is the impact aggregator?</AccordionSummary>
        <AccordionDetails>
          The impact aggregator is a function that groups the impacts of vulnerabilities in order to use them as weights for trading. The
          two functions currently available are the average and the weighted average.
        </AccordionDetails>
      </Accordion>
    </div>
  )
}

export { HelpPage }
