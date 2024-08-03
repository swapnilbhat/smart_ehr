import React from 'react';
import {ReactTyped} from 'react-typed';

const Information = ({ messages }) => {
  if (messages.length === 0) {
    return (
      <div className="text-white flex-1">
        <div className="max-w-[800px] mt-[-200px] w-full h-screen mx-auto text-center flex flex-col justify-center">
          <h1 className="w-full text-4xl font-bold text-[#f3f1fa]">EHR Assistant</h1>
          <h1 className="w-full text-2xl mt-20 font-bold text-[#f3f1fa]">How can I help you today?</h1>
          <div className="mt-5">
            <ReactTyped
              className="w-full text-xl mt-10 font-bold text-[#b1b1b5]"
              strings={['Create a new report', 'Update an existing report', 'Search through your database']}
              typeSpeed={150}
              backSpeed={200}
              loop
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-10 px-20 flex flex-col h-full max-w-[1350px] mx-auto p-4 overflow-y-auto rounded-lg">
      {messages.map((message, index) => (
        <div key={index} className={`mb-2 text-[#f3f1fa]  bg-slate-700 rounded-lg  p-2 max-w-xs ${
          message.sender === 'User' ? 'self-start' : 'self-end'
        }`}>
          <strong>{message.sender}:</strong> {message.text}
        </div>
      ))}
    </div>
  );
  // return (
  //   <div className="mt-10 px-20 flex-1 flex flex-col h-full max-w-[1350px] mx-auto p-4 overflow-y-auto rounded-lg">
  //     {messages.map((message, index) => (
  //       <div key={index} className={`mb-2 text-[#f3f1fa]  bg-slate-700 rounded-lg  p-2 max-w-xs ${
  //         message.sender === 'User' ? 'self-start' : 'self-end'
  //       }`}>
  //         <strong>{message.sender}:</strong> {message.text}
  //       </div>
  //     ))}
  //   </div>
  // );
};

export default Information;
