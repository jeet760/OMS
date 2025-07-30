//#region pincode based lgd details and respective selections
function fetch_districts(statecode, district, sub_district, form) {
    if (statecode != null && statecode !== '') {
        const userDistrict = form.querySelector('.userDistrict');

        if (!userDistrict) {
            console.error('No .userDistrict element found in form.');
            return;
        }

        // Clear the select and then load
        userDistrict.options.length = 0;

        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.text = 'Select District';
        userDistrict.appendChild(defaultOption);

        const api = `https://api.data.gov.in/resource/37231365-78ba-44d5-ac22-3deec40b9197?api-key=579b464db66ec23bdd0000011c8e390297d348f14342ed5a091d6a99&format=json&limit=1000&filters%5Bstate_code%5D=${statecode}`;
        
        fetch(api)
            .then(response => response.json())
            .then(data => {
                if (Array.isArray(data.records)) {
                    data.records.sort((a, b) => a.district_name_english.localeCompare(b.district_name_english));

                    for (const record of data.records) {
                        const option = document.createElement('option');
                        option.value = record.district_code;
                        option.text = record.district_name_english;
                        userDistrict.appendChild(option);
                    }

                    if(!isNaN(district)){
                        userDistrict.value = district;
                    }
                    else{
                        let arr_districts = [];
                        for (let i = 0; i < userDistrict.options.length; i++) {
                            arr_districts.push(userDistrict.options[i].text);
                        }
                        
                        const matchedDistrict = fuzzySearch(district, arr_districts);
                        for (let i = 0; i < userDistrict.options.length; i++) {
                            if (userDistrict.options[i].text === matchedDistrict[0]) {
                                userDistrict.selectedIndex = i;
                                break;
                            }
                        }
                    }

                    const selectedStateCode = form.querySelector('.userState')?.value;
                    const selectedDistrictCode = userDistrict.value;

                    fetch_subdistricts(selectedStateCode, selectedDistrictCode, sub_district, form);
                } else {
                    console.error("Expected 'records' to be an array.");
                }
            })
            .catch(error => {
                console.error('Error fetching district data:', error);
            });
    }
}

function levenshteinDistance(a, b) {
  const matrix = Array.from({ length: b.length + 1 }, (_, i) => [i]);

  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j;
  }

  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      const cost = b[i - 1] === a[j - 1] ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,     // Deletion
        matrix[i][j - 1] + 1,     // Insertion
        matrix[i - 1][j - 1] + cost // Substitution
      );
    }
  }

  return matrix[b.length][a.length];
}

// function fuzzySearch(query, list, threshold = 70) {
//   query = query.toLowerCase();
//   return list.filter(item => {
//     const itemLower = item.toLowerCase();
//     const distance = levenshteinDistance(query, itemLower);
//     const maxLen = Math.max(query.length, itemLower.length);
//     const similarity = ((maxLen - distance) / maxLen) * 100;
//     return similarity >= threshold;
//   });
// }

function fuzzySearch(query, items, threshold = 70) {
  query = query.toLowerCase();
  const results = [];

  for (const item of items) {
    const itemLower = item.toLowerCase();
    const distance = levenshteinDistance(query, itemLower);
    const maxLen = Math.max(query.length, itemLower.length);
    const similarity = ((maxLen - distance) / maxLen) * 100;

    if (similarity >= threshold) {
      results.push(item);
    }
  }

  if (results.length === 0 && threshold > 50) {
    return fuzzySearch(query, items, 50); // recursive fallback
  }

  return results;
}

function fetch_subdistricts(statecode, districtcode, sub_district, form) {
    if (districtcode != null && districtcode !== '') {
        const userCity = form.querySelector(".userCity");

        if (!userCity) {
            console.error("No .userCity element found in form.");
            return;
        }

        // Clear existing options
        userCity.options.length = 0;

        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.text = 'Select Block/Sub-District';
        userCity.appendChild(defaultOption);

        const api = `https://api.data.gov.in/resource/6be51a29-876a-403a-a6da-42fde795e751?api-key=579b464db66ec23bdd0000011c8e390297d348f14342ed5a091d6a99&format=json&limit=1000&filters%5Bstate_code%5D=${statecode}&filters%5Bdistrict_code%5D=${districtcode}`;

        fetch(api)
            .then(response => response.json())
            .then(data => {
                data.records.sort((a, b) => a.subdistrict_name_english.localeCompare(b.subdistrict_name_english));

                if (Array.isArray(data.records)) {
                    for (const record of data.records) {
                        const option = document.createElement('option');
                        option.value = record.subdistrict_code;
                        option.text = record.subdistrict_name_english;
                        userCity.appendChild(option);
                    }

                    if(!isNaN(sub_district)){
                        userCity.value = sub_district;
                    }
                    else{
                        const arr_subdistricts = [];
                        for (let i = 0; i < userCity.options.length; i++) {
                            arr_subdistricts.push(userCity.options[i].text);
                        }

                        const matchedSubdistrict = fuzzySearch(sub_district, arr_subdistricts);
                        for (let i = 0; i < userCity.options.length; i++) {
                            if (userCity.options[i].text === matchedSubdistrict[0]) {
                                userCity.selectedIndex = i;
                                break;
                            }
                        }
                    }
                } else {
                    console.error("Expected 'records' to be an array.");
                }
            })
            .catch(error => {
                console.error("Error fetching subdistrict data:", error);
            });
    }
}

//#endregion
//#region filter table 

/**
   * Generic table filter function
   * @param {string} keyword - value to filter by (e.g., "Pending", "1", "All")
   * @param {string} tableId - id of the table to filter
   * @param {string} dataAttr - attribute used for filtering (e.g., 'source', 'status')
   */
function filterTable(keyword, tableId, dataAttr = 'source') {
    const rows = document.querySelectorAll(`#${tableId} tbody tr`);

    rows.forEach(row => {
      const value = row.dataset[dataAttr];
      if (keyword === 'All') {
        row.style.display = '';
      } else {
        if (value === keyword) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      }
    });
}

function paginate(tableId) {
    const  rowsPerPage = 10;
    const rows = document.querySelectorAll(`#${tableId} tbody tr`);
    const visibleRows = Array.from(rows).filter(row => row.dataset.visible !== "false");
    const totalPages = Math.ceil(visibleRows.length / rowsPerPage);

    rows.forEach(row => row.style.display = 'none');

    visibleRows.forEach((row, index) => {
        row.style.display = (index >= (currentPage - 1) * rowsPerPage && index < currentPage * rowsPerPage) ? '' : 'none';
    });

    const pagination = document.getElementById('pagination');
    if (pagination){
        pagination.innerHTML = '';
        for (let i = 1; i <= totalPages; i++) {
            const btn = document.createElement('button');
            btn.textContent = i;
            btn.className = 'px-3 py-1 rounded bg-gray-700 text-white mx-1';
            if (i === currentPage) btn.classList.add('bg-blue-600');
            btn.onclick = () => {
                currentPage = i;
                paginate();
            };
            pagination.appendChild(btn);
        }
    }
}
//#endregion