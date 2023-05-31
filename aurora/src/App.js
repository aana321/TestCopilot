import React from 'react';
import HomePage from './HomePage';
import Chat from './Chat';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import './style.css';


function App() {
  return (
    <Router>
      <Routes>
        <Route path="/home" element={<HomePage />} />
        <Route path="/" element={<Navigate replace to="/home" />} />
        <Route path="/chat"  element={<Chat/>} />
      </Routes>
    </Router>
  );
}

export default App;
