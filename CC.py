#!/usr/bin/env python
# coding: utf-8

# In[1]:


import random


# In[2]:


def hotel():
    asked_hotel = random.getrandbits(1)
    return asked_hotel


# In[3]:


def plane():
    asked_plane = random.getrandbits(1)
    return asked_plane


# In[4]:


from concurrent.futures import ThreadPoolExecutor
from flask import Flask, escape, request

def intermediary():
    with ThreadPoolExecutor(max_workers=4) as executor:
        hotel1 = executor.submit(hotel)
        plane1 = executor.submit(plane)
        if hotel1.result() == 1 and plane1.result() == 1:
          print("1 completed")
        else:
          print("1 uncompleted")
        
        hotel2 = executor.submit(hotel)
        plane2 = executor.submit(plane)
        if hotel2 == 1 and plane2 == 1:
          print("2 completed")
        else:
          print("2 uncompleted")

intermediary()


# In[ ]:




