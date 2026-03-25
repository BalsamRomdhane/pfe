/*
  standards.js provides a modern management UI for standards and controls.
*/

(function () {

  function initStandards() {

    const STANDARDS_API_ENDPOINT = "/api/standards/";
    const tableBody = document.querySelector("#standardsTable tbody");
    const modalElement = document.getElementById("standardModal");

    const createForm = document.getElementById("create-standard-form");
    const createBtn = document.getElementById("create-standard-btn");
    const cancelCreateBtn = document.getElementById("cancel-create-btn");

    const editName = document.getElementById("editStandardName");
    const editDescription = document.getElementById("editStandardDescription");

    const controlsContainer = document.getElementById("controlsContainer");
    const newControlInput = document.getElementById("newControlInput");
    const addControlBtn = document.getElementById("addControlBtn");

    const editForm = document.getElementById("standardEditForm");
    const closeModalBtn = document.getElementById("closeModal");
    const cancelEditBtn = document.getElementById("cancelEditBtn");

    const controlsModal = document.getElementById("controlsModal");
    const controlsModalTitle = document.getElementById("controlsModalTitle");
    const controlsList = document.getElementById("controlsList");
    const closeControlsModalBtn = document.getElementById("closeControlsModal");

    let currentStandard = null;
    let currentControls = [];
    let deletedControlIds = new Set();


    /* -------------------------------
       Helpers
    --------------------------------*/

    const getHeaders = (extra = {}) => {
      return typeof addCsrfHeader === "function"
        ? addCsrfHeader(extra)
        : extra;
    };


    const safeFetch = async (url, options = {}) => {
      try {
        const response = await fetch(url, options);

        if (!response.ok) {
          const text = await response.text();
          console.error("API error:", text);
          throw new Error(text);
        }

        return response;
      } catch (error) {
        console.error("Network error:", error);
        throw error;
      }
    };


    /* -------------------------------
       Modal Management
    --------------------------------*/

    const showModal = () => modalElement?.classList.remove("hidden");

    const hideModal = () => {
      modalElement?.classList.add("hidden");
      currentStandard = null;
      currentControls = [];
      deletedControlIds.clear();
    };


    const showControlsModal = (standard) => {

      if (!controlsModal) return;

      controlsModalTitle.textContent = `${standard.name} Controls`;
      controlsList.innerHTML = "";

      const controls = standard.controls || [];

      if (!controls.length) {
        controlsList.innerHTML =
          `<p class="text-gray-500 text-sm">No controls defined.</p>`;
      } else {

        controls.forEach((control, index) => {

          const div = document.createElement("div");

          div.className =
            "flex items-start gap-3 p-3 bg-gray-50 rounded-lg";

          div.innerHTML = `
            <span class="w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-xs font-medium">
              ${index + 1}
            </span>
            <p class="text-sm text-gray-700">${control.description}</p>
          `;

          controlsList.appendChild(div);
        });
      }

      controlsModal.classList.remove("hidden");
    };


    const hideControlsModal = () =>
      controlsModal?.classList.add("hidden");


    /* -------------------------------
       Fetch & Render
    --------------------------------*/

    const fetchStandards = async () => {

      try {

        const response = await safeFetch(STANDARDS_API_ENDPOINT);
        const standards = await response.json();

        renderStandards(standards);

      } catch (err) {

        console.error("Failed loading standards");

      }

    };


    const renderStandards = (standards = []) => {

      if (!tableBody) return;

      tableBody.innerHTML = "";

      if (!standards.length) {

        tableBody.innerHTML = `
          <tr>
            <td colspan="4"
              class="px-6 py-8 text-center text-gray-500">
              No standards found.
            </td>
          </tr>
        `;

        return;
      }


      standards.forEach((standard) => {

        const controls = standard.controls || [];
        const firstControl =
          controls.length ? controls[0].description : "No controls";

        const tr = document.createElement("tr");

        tr.className =
          "border-b border-gray-100 hover:bg-gray-50 cursor-pointer";

        tr.innerHTML = `

          <td class="px-6 py-4 text-sm font-medium">
            ${standard.name}
          </td>

          <td class="px-6 py-4 text-sm">
            ${standard.description || ""}
          </td>

          <td class="px-6 py-4 text-sm">

            <div class="flex items-center gap-2">

              <span class="truncate max-w-48 flex-1">
                ${firstControl}
              </span>

              <span class="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                ${controls.length}
              </span>

            </div>

          </td>

          <td class="px-6 py-4">

            <button
              data-edit="${standard.id}"
              class="text-blue-600 mr-2">
              Edit
            </button>

            <button
              data-delete="${standard.id}"
              class="text-red-600">
              Delete
            </button>

          </td>
        `;


        tr.addEventListener("click", (e) => {
          if (e.target.closest("[data-edit]") ||
              e.target.closest("[data-delete]")) return;

          showControlsModal(standard);
        });


        tableBody.appendChild(tr);
      });


      tableBody.querySelectorAll("[data-delete]")
        .forEach(btn => {

          btn.onclick = async (e) => {

            e.stopPropagation();

            if (!confirm("Delete standard ?")) return;

            await safeFetch(
              `${STANDARDS_API_ENDPOINT}${btn.dataset.delete}/`,
              {
                method: "DELETE",
                headers: getHeaders(),
                credentials: "same-origin"
              }
            );

            fetchStandards();
          };

        });


      tableBody.querySelectorAll("[data-edit]")
        .forEach(btn => {

          btn.onclick = (e) => {

            e.stopPropagation();

            const standard =
              standards.find(s => s.id == btn.dataset.edit);

            if (standard) openEditModal(standard);
          };

        });

    };


    /* -------------------------------
       Controls Management
    --------------------------------*/

    const openEditModal = (standard) => {

      currentStandard = standard;

      currentControls = (standard.controls || [])
        .map(c => ({ ...c }));

      editName.value = standard.name || "";
      editDescription.value = standard.description || "";

      renderControls();
      showModal();
    };


    const renderControls = () => {

      controlsContainer.innerHTML = "";

      currentControls.forEach(control => {

        const row = document.createElement("div");

        row.className =
          "flex gap-2 items-center mb-2";

        const input = document.createElement("input");

        input.value = control.description;

        input.className =
          "flex-1 border px-2 py-1 rounded";

        input.oninput = e =>
          control.description = e.target.value;


        const del = document.createElement("button");

        del.innerHTML = "Delete";

        del.className =
          "text-red-600";

        del.onclick = () => {

          if (control.id)
            deletedControlIds.add(control.id);

          currentControls =
            currentControls.filter(c => c !== control);

          renderControls();
        };


        row.append(input, del);
        controlsContainer.appendChild(row);

      });

    };


    const addControl = () => {

      const value = newControlInput.value.trim();

      if (!value) return;

      currentControls.push({
        description: value
      });

      newControlInput.value = "";

      renderControls();
    };


    /* -------------------------------
       Save Standard
    --------------------------------*/

    const saveStandard = async (e) => {

      e.preventDefault();

      const id = currentStandard.id;

      await safeFetch(
        `${STANDARDS_API_ENDPOINT}${id}/`,
        {
          method: "PATCH",
          headers: getHeaders({
            "Content-Type": "application/json"
          }),
          credentials: "same-origin",
          body: JSON.stringify({
            name: editName.value,
            description: editDescription.value
          })
        }
      );


      for (const controlId of deletedControlIds) {

        await safeFetch(
          `${STANDARDS_API_ENDPOINT}${id}/controls/${controlId}/`,
          {
            method: "DELETE",
            headers: getHeaders(),
            credentials: "same-origin"
          }
        );

      }


      for (const control of currentControls) {

        const method = control.id ? "PATCH" : "POST";

        const url = control.id
          ? `${STANDARDS_API_ENDPOINT}${id}/controls/${control.id}/`
          : `${STANDARDS_API_ENDPOINT}${id}/controls/`;

        await safeFetch(
          url,
          {
            method,
            headers: getHeaders({
              "Content-Type": "application/json"
            }),
            credentials: "same-origin",
            body: JSON.stringify({
              description: control.description
            })
          }
        );

      }


      hideModal();
      fetchStandards();
    };


    /* -------------------------------
       Events
    --------------------------------*/

    createBtn?.addEventListener("click",
      () => createForm?.classList.remove("hidden"));

    cancelCreateBtn?.addEventListener("click",
      () => createForm?.classList.add("hidden"));

    addControlBtn?.addEventListener("click", addControl);

    newControlInput?.addEventListener("keydown", e => {

      if (e.key === "Enter") {

        e.preventDefault();
        addControl();

      }

    });


    editForm?.addEventListener("submit", saveStandard);

    closeModalBtn?.addEventListener("click", hideModal);
    cancelEditBtn?.addEventListener("click", hideModal);

    closeControlsModalBtn?.addEventListener("click",
      hideControlsModal);


    fetchStandards();
  }

  window.initStandards = initStandards;

})();