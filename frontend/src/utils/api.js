
/* * LUMINA - AI-POWERED RECEIPT MANAGEMENT 
 SYSTEM
  * API Utilities with Automatic Backend Detection and Retry Logic
   * 
    * Copyright (c) 2024 Jaideep Singh Rajpurohit. All rights reserved.
     * PROPRIETARY SOFTWARE - UNAUTHORIZED USE PROHIBITED
      */


// --------------------------------------------------


//import axios from "axios";


/* LUMINA - AI-POWERED RECEIPT MANAGEMENT SYSTEM
   FIXED API CLIENT FOR PRODUCTION
*/

export const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "https://luminaocr.com/api";

console.log("Using Backend:", API_BASE_URL);

const api = {
  // GET
  async get(path) {
    const res = await fetch(`${API_BASE_URL}${path}`);
    if (!res.ok) throw new Error(`GET failed: ${res.status}`);
    return res.json();
  },

  // POST (generic)
  async post(path, data) {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: typeof data === "object" && !(data instanceof FormData)
        ? { "Content-Type": "application/json" }
        : undefined,
      body: data instanceof FormData ? data : JSON.stringify(data),
    });

    if (!res.ok) throw new Error(`POST failed: ${res.status}`);
    return res.json();
  },

  // UPLOAD RECEIPT
  async upload(formData) {
    const res = await fetch(`${API_BASE_URL}/receipts`, {
      method: "POST",
      body: formData,
    });

    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json();
  },

  // DELETE
  async delete(path) {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: "DELETE",
    });

    if (!res.ok) throw new Error(`DELETE failed: ${res.status}`);
    return res.json();
  },

  // PUT
  async put(path, data) {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (!res.ok) throw new Error(`PUT failed: ${res.status}`);
    return res.json();
  },
};

export default api;
