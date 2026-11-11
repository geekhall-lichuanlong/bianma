// src/api/history.js
import axios from 'axios'

// const API_BASE_URL = 'https://api.example.com' // Replace with your actual API base URL

const API_BASE_URL = 'http://localhost:3001'
export const fetchHistory = async (type, id) => {
  try {
    console.log(`Fetching history for type: ${type}, id: ${id}`)
    const response = await axios.get(`${API_BASE_URL}/${type}`)
    return response.data
  } catch (error) {
    console.error(`Error fetching ${type} history:`, error)
    throw error
  }
}

export const saveHistoryItem = async (type, id, item) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/${type}`, item)
    return response.data
  } catch (error) {
    console.error(`Error saving ${type} history item:`, error)
    throw error
  }
}
