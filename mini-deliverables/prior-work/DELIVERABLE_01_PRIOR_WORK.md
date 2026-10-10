# Deliverable 1: Prior Work and Project Direction

## Three primary references

1. Jung, Paul H., and Jun Song. “Multivariate Neighborhood Trajectory Analysis: An Exploration of the Functional Data Analysis Approach.” *Geographical Analysis*, vol. 54, no. 4, 2022, pp. 789–819, [https://doi.org/10.1111/gean.12298](https://doi.org/10.1111/gean.12298).

   This paper gives us a concrete starting point for grouping communities by how they change, not just by how they look in one year. The authors use 16 Census variables from 1970 through 2010 and combine multivariate functional principal component analysis with k-means to perform their neighborhood analysis. We would treat that as a baseline while testing whether more frequent, non-overlapping ACS periods can produce useful trajectories without ignoring the ACS's uncertainty.

2. Wang, Zhecheng, Haoyuan Li, and Ram Rajagopal. “Urban2Vec: Incorporating Street View Imagery and POIs for Multi-Modal Urban Neighborhood Embedding.” *Proceedings of the AAAI Conference on Artificial Intelligence*, vol. 34, no. 1, 2020, pp. 1013–1020, [https://doi.org/10.1609/aaai.v34i01.5450](https://doi.org/10.1609/aaai.v34i01.5450). [Open PDF](https://ojs.aaai.org/index.php/AAAI/article/download/5450/5306).

   This is the closest reference found to how we picture the community similarity matching part of the project: neighborhoods are represented as vectors and then matched across cities rather than only with nearby areas. Its use of Google Street View, Yelp, and a separate real estate dataset would be difficult to reproduce nationally under our access requirements and timeline, so we might just borrow the representation and retrieval idea while first building it from consistent public data and comparing it with simpler/more explainable similarity measures.

3. Francke, Marc, Lyndsey Rolheiser, and Alex Van de Minne. “Estimating Census Tract House Price Indexes: A New Spatial Dynamic Factor Approach.” *The Journal of Real Estate Finance and Economics*, vol. 70, 2025, pp. 483–514, [https://doi.org/10.1007/s11146-023-09957-w](https://doi.org/10.1007/s11146-023-09957-w).

   This paper changed how we think about modeling housing trends in tracts with limited observations because it shows the value of borrowing information from shared market patterns and spatially related areas. We would not try to reproduce its proprietary Rezitrade transaction dataset; instead, we would test the same general idea with the public FHFA tract level data and ask whether spatial and metropolitan context improve future forecasts without missing real local differences.

## Additional references shaping the project

These references are useful to the larger project direction, but the three sources above are the formal response for this assignment.

### Athid et al.: digital-twin scenarios

Athid, Rakibun, et al. “A Digital Twin to Improve the Sustainability of Neighbourhood Scenario Planning.” *ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences*, vol. XII-4/W2-2026, 2026, pp. 17–24, [https://doi.org/10.5194/isprs-annals-XII-4-W2-2026-17-2026](https://doi.org/10.5194/isprs-annals-XII-4-W2-2026-17-2026).

This paper helped us draw a clearer line between an interactive dashboard and a useful digital twin. We want our scenario controls to represent understandable assumptions about our data, stay within realistic ranges, and show sensitivity instead of giving users a collection of sliders that imply more certainty or control than the model can support. The key point here is to focus on simplisity and explainability in our design or even reduce geographic scope while testing to keep iterations moving forward with good feedback.

### The Opportunity Atlas: application design

Chetty, Raj, et al. “The Opportunity Atlas: Mapping the Childhood Roots of Social Mobility.” *American Economic Review*, vol. 116, no. 1, 2026, pp. 1–51, [https://doi.org/10.1257/aer.20200108](https://doi.org/10.1257/aer.20200108). [*The Opportunity Atlas* interactive application](https://www.opportunityatlas.org/).

The Opportunity Atlas is a useful design reference because it makes complicated Census tract level research approachable through a central map and supporting analytical panels on either side. It gives us an idea for our application to have that same clarity while going further into community histories, similarity matching, forecasts, and scenario exploration.

### Zillow AI Mode: conversational exploration

“Zillow Debuts AI Mode, a Smarter Way to Find and Afford Your Next Home.” *Zillow MediaRoom*, Zillow, 25 Mar. 2026, [https://www.zillow.com/news/zillow-debuts-ai-mode/](https://www.zillow.com/news/zillow-debuts-ai-mode/). Accessed 10 Oct. 2026.

Zillow's AI Mode gives a clearer picture of how a conversational assistant could complement the map instead of replacing it. A user might ask why two communities were matched or request places similar in affordability but different in housing supply, and the assistant should answer by calling our actual data and models and showing the evidence behind its response.

## Data and geographic direction

The project should use a **national comparison pool wherever the core public data supports it**. Matching across geographic regions is part of the research question: a community in Michigan may have a more informative/interesting analogue in Ohio, Pennsylvania, Wisconsin, North Carolina, or somewhere less obvious than in the tract next door.

The three research papers are useful for their methods, but none should dictate our exact data pipeline. Jung and Song use harmonized historical Census data on 2010 tract boundaries, Urban2Vec relies on API and commercial data sources, and Francke and coauthors use a prepared transaction dataset that is not openly reproducible. Our core should instead favor nationally consistent sources that every teammate can access, such as ACS, FHFA, Census geography and relationship files, and selected public economic or environmental sources.

That does not require every feature or application view to have identical national depth. We can build a consistent nationwide core and use a geographically varied set of demonstration metros for closer evaluation, qualitative review of similarity matches, and application testing. If a later scope cut is necessary, a diverse multi-region sample would preserve the matching across communities question better than limiting the project to Michigan.
