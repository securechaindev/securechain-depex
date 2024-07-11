import React from 'react'
import { RouterProvider, createBrowserRouter, Outlet } from 'react-router-dom'
import { Home, Boxes, CircleHelp } from 'lucide-react'
import { HomePage } from '../homePage/home'
import { HelpPage } from '../helpPage/help'
import { LoginPage } from '../auth/login'
import { SignUpPage } from '../auth/signup'
import { RepositoriesPage } from '../repositoriesPage/repositories'
import Sidebar, { SidebarItem } from '../components/sidebar'
import { ProtectedRoute } from '../auth/protectedRoute'

function Routes() {
  const isLoggedIn = () => {
    const acess_token = localStorage.getItem('acess_token')
    // Comprobar que el token sea válido
    // const valid_token = null
    if (acess_token === null) {
      return false
    } else {
      return true
    }
  }

  const SidebarLayout = () => (
    <>
      <Sidebar isLoggedIn={isLoggedIn()}>
        <SidebarItem icon={<Home size={20} />} text='Home' route='/' />
        {isLoggedIn() ? <SidebarItem icon={<Boxes size={20} />} text='Repositories' route='/repositories' /> : null}
        <SidebarItem icon={<CircleHelp size={20} />} text='Help' route='/help' />
      </Sidebar>
      <Outlet />
    </>
  )

  const routesForSidebar = [
    {
      path: '/',
      element: <HomePage isLoggedIn={isLoggedIn()} />
    },
    {
      path: '/login',
      element: <LoginPage />
    },
    {
      path: '/signup',
      element: <SignUpPage />
    },
    {
      path: '/help',
      element: <HelpPage />
    },
    {
      path: '/',
      element: <ProtectedRoute />,
      children: [
        {
          path: '/repositories',
          element: <RepositoriesPage />
        }
      ]
    }
  ]

  const routesForPublic = [
    {
      path: '/',
      element: <HomePage isLoggedIn={isLoggedIn()} />
    },
    {
      path: '/login',
      element: <LoginPage />
    },
    {
      path: '/signup',
      element: <SignUpPage />
    },
    {
      path: '/help',
      element: <HelpPage />
    }
  ]

  const routesForAuthenticatedOnly = [
    {
      path: '/',
      element: <ProtectedRoute />,
      children: [
        {
          path: '/repositories',
          element: <RepositoriesPage />
        }
      ]
    }
  ]

  const router = createBrowserRouter([
    {
      element: <SidebarLayout />,
      children: [...routesForSidebar]
    },
    ...routesForPublic,
    ...routesForAuthenticatedOnly
  ])

  return <RouterProvider router={router} />
}

export default Routes
