import React from 'react'
import logo from '../assets/as_logo.png'; 
const Navbar = () => {
  return (
    <div className='text-white flex justify-between items-center h-24 max-w-[1350px] mx-auto px-4'>
      <img src={logo} alt="Logo" className='w-30 h-20 mt-2'/>
      <ul className='flex'>
        <li className='p-4'>Home</li>
        <li className='p-4'>About</li>
        <li className='p-4'>Contact</li>
      </ul>
    </div>
  )
}

export default Navbar
