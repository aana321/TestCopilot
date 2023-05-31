import React from "react";
import { useNavigate} from 'react-router-dom';
import './home.css';
import Logo from './rattle_logo.svg';

function LandingPage() {
    const navigate = useNavigate();

    const onButtonClick = () => {
      navigate('/chat');
    };
  
    return (
      <div className="homepage">
        <h1 className="landing-page-heading">RATTLE RELIABILITY COPILOT</h1>
        <img src={Logo} alt="Logo" className="logo" />
      
        <div className="button-container">
          <button className="button" onClick={onButtonClick}>
            Try Now!
            </button>
          <button className="button" onClick={onButtonClick}>
            Join Waitlist!
          </button>
        </div>  
      
        <p className="powered-by">Powered by Jio Fynd</p>
    </div>

  );

  }

  export default LandingPage