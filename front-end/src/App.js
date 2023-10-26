import "./App.css";
import React from "react";

import { Route, BrowserRouter, Routes } from "react-router-dom";
import SearchDoc from "./pages/main-search/MainSearchDoc";
import CommonTopNav from "./pages/top-navication/common-top-navication";

function App() {
  return (
    <div>
      <CommonTopNav />
      <BrowserRouter>
        <Routes>
          <Route exact path="/" element={<SearchDoc />} key="/" />
          <Route exact path="/search" element={<SearchDoc />} key="/search" />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
