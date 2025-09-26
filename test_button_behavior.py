#!/usr/bin/env python3
"""
Simple test to verify button behavior in Streamlit
"""

import streamlit as st
import time

def main():
    st.title("Button Test")

    # Initialize session state
    if 'clicked' not in st.session_state:
        st.session_state.clicked = False
        st.session_state.click_count = 0

    # Test button
    if st.button("Test Button", type="primary"):
        st.session_state.clicked = True
        st.session_state.click_count += 1
        st.success(f"Button clicked! Count: {st.session_state.click_count}")

    # Show status
    st.write(f"Button was clicked: {st.session_state.clicked}")
    st.write(f"Click count: {st.session_state.click_count}")

    # Test file upload
    uploaded_file = st.file_uploader("Test upload", type=['pdf'])
    st.write(f"File uploaded: {uploaded_file is not None}")

    # Test button with conditions
    can_process = uploaded_file is not None
    if st.button("Conditional Button", disabled=not can_process):
        st.success("Conditional button works!")

    # Test debug info
    if st.checkbox("Show Debug"):
        st.write("Debug Info:")
        st.write(f"- Session state: {dict(st.session_state)}")
        st.write(f"- File object: {uploaded_file}")

if __name__ == "__main__":
    main()