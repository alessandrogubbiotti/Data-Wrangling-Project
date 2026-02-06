## Epstein Files: Exploratory Data Analysis

We analyze the documents that have been released by the [U.S. Department of Justice](https://www.justice.gov), the infamous [Epstein Files](https://www.justice.gov/epstein)


### The Raw Data: DOJ Epstein Files – Public Dataset Batches Overview

The subdivision of the Epstein files into datasets is **purely administrative**.

These datasets were created based on:

- FOIA processing workflow
- Legal clearance and redaction completion
- Record storage origin
- Technical packaging constraints
- Chronological order of public release

They are not organized by investigative topic, individuals, or case narrative structure.
---

**Dataset 1**
<!--**General Content:**  
Early investigative records, primarily Florida case materials and supporting FBI documentation.-->

**Approximate Size:** ~6–8 GB

---

**Dataset 2**
<!--**General Content:**  
Additional Florida prosecution records and supporting evidence expansions.-->
Approximate Size: ~8–10 GB

---

**Dataset 3**
<!--**General Content:**  
Early SDNY (New York federal prosecution) investigative materials and case exhibits.-->
Approximate Size: ~9–11 GB

---

**Dataset 4**
<!--**General Content:**  
Ghislaine Maxwell case-related exhibits and prosecution evidence attachments.
-->
**Approximate Size:** ~7–9 GB

---

**Dataset 5**
<!--**General Content:**  
FBI operational investigative files including reports, interview summaries, and evidence logs.
-->
Approximate Size: ~10–12 GB

---

**Dataset 6**
<!--**General Content:**  
DOJ Inspector General supporting documentation and internal review materials.
-->
Approximate Size: ~5–7 GB

---

**Dataset 7**
<!--**General Content**:  
Supplemental FOIA release materials including additional evidence files and document scans.
-->
Approximate Size: ~11–13 GB

---

**Dataset 8**
<!--**General Content:**  
Additional supplemental FOIA batch containing mixed evidence, communications, and document attachments.
-->
Approximate Size: ~10–12 GB

---

**Dataset 9**
<!--**General Content:**  
Late-stage supplemental FOIA disclosures including supporting case records and metadata packages.
-->
Approximate Size: ~9–11 GB

---

**Dataset 10**
<!--**General Content**:  
Media-heavy evidence grouping, primarily:

- Images
- Video evidence
- Multimedia attachments
-->
Approximate Size: ~30–40 GB

---

**Dataset 11**
<!--**General Content:**  
Final addenda and additional disclosures including estate-related and late-cleared documentation.-->

Approximate Size: ~3–5 GB

---


#### The Dataset with which we work 

One of the problems to addres befor doing any data analysis is to parse the text of the documents that are saved as images. Then, there is the problem of obtaining information from them such as subject of the e-mail, the context, people taking part in them ...  
Fortunately, many different github folders that have been developed for this precise scope 
*[First GitHub page (it uses AI to parse text and names)](https://github.com/epstein-docs/epstein-docs.github.io)

[Second GitHub page](https://github.com/markramm/EpsteinFiles)

[Third GitHub page](https://github.com/actuallyrizzn/epstein-browser)

[The program used by a journalist](https://buttondown.com/readwrite/archive/edition-9-searching-through-the-epstein-files/)

We use the data extracted by the first one of them. 
 
#### The aim of our Analysis

A lot of effort in an interactive visualization and has been put in the work of the github user [GitHub page](https://github.com/epstein-docs/epstein-docs.github.io). In particular, we ca easily search through the parsed files, filtering them interactively, by the [github pages site](https://epstein-docs.github.io) . Even more than that, he made [an interactive graph](https://epsteinvisualizer.com) whose nodes are the people, institutions, countries, and the edges is if both nodes are found in the same email (I have to check this), and made an interactive graph 
...to be constructed


#### Censorship

- One of the problems we have to deal with is the censorship. Indeed, the distribution of the names we obtain is biased by the fact that only the names that have not been "blanked" -- and from the documents that have actually been published, are analyzed

- Moreover, it seems that, by some [Reddit posts](https://www.reddit.com/r/DataHoarder/comments/1qsfv3j/epstein_9_10_11_12_reddit_keeps_nuking_thread_we/), the dataset 9 contains particularly compromising information, as it has been leaked by error and has been forcefully removed from the internet


#### Curiosities

- The (speculated, but very likely, to be) [Reddit profile of Ghislane Maxwell](https://www.reddit.com/user/maxwellhill/)
- https://www.jmail.world

#### Disclaimer

The choice of the dataset is due to me and only to me. Some Epstein files have been leaked illegaly from the  and are not present in this data








