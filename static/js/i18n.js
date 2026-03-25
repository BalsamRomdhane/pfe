/**
 * Internationalization (i18n) system for ComplianceAI
 * Supports English and French
 */

const i18n = {
  currentLanguage: localStorage.getItem('language') || 'en',
  
  translations: {
    en: {
      // Navigation
      'nav.dashboard': 'Dashboard',
      'nav.upload': 'Upload',
      'nav.documents': 'Documents',
      'nav.standards': 'Standards',
      'nav.audit': 'Audit',
      'nav.analytics': 'Analytics',
      'nav.chat': 'AI Assistant',
      'nav.settings': 'Settings',

      // Navigation Sections
      'nav.section.core': 'Core',
      'nav.section.compliance': 'Compliance',
      'nav.section.ai': 'AI',
      'nav.section.system': 'System',

      // Menu
      'menu.settings': 'Settings',
      'menu.help': 'Help',
      'menu.signout': 'Sign out',
      
      // Common
      'common.search': 'Search',
      'common.filter': 'Filter',
      'common.apply': 'Apply',
      'common.close': 'Close',
      'common.delete': 'Delete',
      'common.edit': 'Edit',
      'common.save': 'Save',
      'common.cancel': 'Cancel',
      'common.loading': 'Loading...',
      'common.error': 'Error',
      'common.success': 'Success',
      'common.warning': 'Warning',
      'common.info': 'Information',
      
      // Documents Page
      'documents.title': 'Documents',
      'documents.subtitle': 'View uploaded documents and delete items when no longer needed.',
      'documents.upload_btn': 'Upload new documents',
      'documents.filter_standard': 'Filter by standard',
      'documents.all_standards': 'All standards',
      'documents.search_placeholder': 'File name or content',
      'documents.delete_selected': 'Delete selected',
      'documents.select_all': 'Select all',
      'documents.analyze': 'Analyze',
      'documents.columns.file': 'File',
      'documents.columns.standard': 'Standard',
      'documents.columns.uploaded': 'Uploaded',
      'documents.columns.actions': 'Actions',
      'documents.no_documents': 'No documents found.',
      'documents.loading': 'Loading documents...',
      'documents.error': 'Failed to load documents.',
      
      // Analysis Modal
      'analysis.title': 'Audit Analysis',
      'analysis.summary': 'Summary',
      'analysis.score': 'Score',
      'analysis.status': 'Status',
      'analysis.compliant': 'Compliant',
      'analysis.partially_compliant': 'Partially Compliant',
      'analysis.non_compliant': 'Non-Compliant',
      'analysis.violations': 'Detected Violations',
      'analysis.total_violations': 'Total',
      'analysis.critical_violations': 'Critical Violations',
      'analysis.missing_controls': 'Missing Controls',
      'analysis.risks': 'Identified Risks',
      'analysis.recommendations': 'Recommendations',
      'analysis.no_analysis': 'No analysis available.',
      'analysis.error': 'Failed to load analysis.',
      'analysis.execute_audit': 'Execute an audit to generate analysis.',
      
      // Upload Page
      'upload.title': 'Upload Documents',
      'upload.subtitle': 'Upload compliance documents for analysis.',
      'upload.select_standard': 'Select a standard',
      'upload.choose_files': 'Choose files',
      'upload.uploading': 'Uploading...',
      'upload.upload_btn': 'Upload',
      'upload.success': 'Documents uploaded successfully!',
      'upload.error': 'Failed to upload documents.',
      
      // Dashboard
      'dashboard.title': 'Dashboard',
      'dashboard.overview': 'Compliance Overview',
      'dashboard.total_documents': 'Total Documents',
      'dashboard.compliant': 'Compliant',
      'dashboard.partially_compliant': 'Partially Compliant',
      'dashboard.non_compliant': 'Non-Compliant',
      'dashboard.recent_audits': 'Recent Audits',
      
      // Audit Results
      'audit.title': 'Audit Results',
      'audit.run_audit': 'Run Audit',
      'audit.select_documents': 'Select documents',
      'audit.select_standard': 'Select standard',
      'audit.run': 'Run',
      'audit.running': 'Audit in progress...',
      'audit.complete': 'Audit complete',
      'audit.error': 'Audit failed',
      
      // Standards
      'standards.title': 'Standards',
      'standards.subtitle': 'Compliance standards and frameworks.',
      'standards.no_standards': 'No standards available.',
      'standards.create': 'Create Standard',
      'standards.create_button': 'Create Standard',
      'standards.table.standard': 'Standard',
      'standards.table.description': 'Description',
      'standards.table.controls': 'Controls',
      'standards.table.actions': 'Actions',
      'standards.controls.title': 'Controls',
      'standards.controls.add': 'Add Control',
      'standards.controls.none': 'No controls defined.',
      
      // Analytics
      'analytics.title': 'Analytics',
      'analytics.subtitle': 'Compliance metrics and trends.',
      'analytics.compliance_rate': 'Compliance Rate',
      'analytics.trend': 'Trend',
      
      // Chat
      'chat.title': 'Compliance Chat',
      'chat.subtitle': 'Ask compliance questions.',
      'chat.message_placeholder': 'Type your question...',
      'chat.send': 'Send',
      
      // Language
      'lang.title': 'Language',
      'lang.english': 'English',
      'lang.french': 'Français',
    },
    
    fr: {
      // Navigation
      'nav.dashboard': 'Tableau de Bord',
      'nav.upload': 'Télécharger',
      'nav.documents': 'Documents',
      'nav.standards': 'Normes',
      'nav.audit': 'Audit',
      'nav.analytics': 'Analytique',
      'nav.chat': 'Assistant IA',
      'nav.settings': 'Paramètres',

      // Navigation Sections
      'nav.section.core': 'Général',
      'nav.section.compliance': 'Conformité',
      'nav.section.ai': 'IA',
      'nav.section.system': 'Système',
      
      // Menu
      'menu.settings': 'Paramètres',
      'menu.help': 'Aide',
      'menu.signout': 'Déconnexion',
      
      // Common
      'common.search': 'Rechercher',
      'common.filter': 'Filtrer',
      'common.apply': 'Appliquer',
      'common.close': 'Fermer',
      'common.delete': 'Supprimer',
      'common.edit': 'Modifier',
      'common.save': 'Enregistrer',
      'common.cancel': 'Annuler',
      'common.loading': 'Chargement...',
      'common.error': 'Erreur',
      'common.success': 'Succès',
      'common.warning': 'Avertissement',
      'common.info': 'Information',
      
      // Documents Page
      'documents.title': 'Documents',
      'documents.subtitle': 'Visualisez les documents téléchargés et supprimez les éléments qui ne sont plus nécessaires.',
      'documents.upload_btn': 'Télécharger de nouveaux documents',
      'documents.filter_standard': 'Filtrer par norme',
      'documents.all_standards': 'Toutes les normes',
      'documents.search_placeholder': 'Nom de fichier ou contenu',
      'documents.delete_selected': 'Supprimer la sélection',
      'documents.select_all': 'Tout sélectionner',
      'documents.analyze': 'Analyser',
      'documents.columns.file': 'Fichier',
      'documents.columns.standard': 'Norme',
      'documents.columns.uploaded': 'Téléchargé',
      'documents.columns.actions': 'Actions',
      'documents.no_documents': 'Aucun document trouvé.',
      'documents.loading': 'Chargement des documents...',
      'documents.error': 'Impossible de charger les documents.',
      
      // Analysis Modal
      'analysis.title': 'Analyse d\'Audit',
      'analysis.summary': 'Résumé',
      'analysis.score': 'Score',
      'analysis.status': 'Statut',
      'analysis.compliant': 'Conforme',
      'analysis.partially_compliant': 'Partiellement Conforme',
      'analysis.non_compliant': 'Non-Conforme',
      'analysis.violations': 'Violations Détectées',
      'analysis.total_violations': 'Total',
      'analysis.critical_violations': 'Violations Critiques',
      'analysis.missing_controls': 'Contrôles Manquants',
      'analysis.risks': 'Risques Identifiés',
      'analysis.recommendations': 'Recommandations',
      'analysis.no_analysis': 'Aucune analyse disponible.',
      'analysis.error': 'Impossible de charger l\'analyse.',
      'analysis.execute_audit': 'Exécutez un audit pour générer l\'analyse.',
      
      // Upload Page
      'upload.title': 'Télécharger des Documents',
      'upload.subtitle': 'Téléchargez des documents de conformité pour analyse.',
      'upload.select_standard': 'Sélectionner une norme',
      'upload.choose_files': 'Choisir les fichiers',
      'upload.uploading': 'Téléchargement en cours...',
      'upload.upload_btn': 'Télécharger',
      'upload.success': 'Documents téléchargés avec succès!',
      'upload.error': 'Impossible de télécharger les documents.',
      
      // Dashboard
      'dashboard.title': 'Tableau de Bord',
      'dashboard.overview': 'Aperçu de la Conformité',
      'dashboard.total_documents': 'Total des Documents',
      'dashboard.compliant': 'Conforme',
      'dashboard.partially_compliant': 'Partiellement Conforme',
      'dashboard.non_compliant': 'Non-Conforme',
      'dashboard.recent_audits': 'Audits Récents',
      
      // Audit Results
      'audit.title': 'Résultats d\'Audit',
      'audit.run_audit': 'Exécuter l\'Audit',
      'audit.select_documents': 'Sélectionner les documents',
      'audit.select_standard': 'Sélectionner la norme',
      'audit.run': 'Exécuter',
      'audit.running': 'Audit en cours...',
      'audit.complete': 'Audit terminé',
      'audit.error': 'Audit échoué',
      
      // Standards
      'standards.title': 'Normes',
      'standards.subtitle': 'Normes de conformité et cadres.',
      'standards.no_standards': 'Aucune norme disponible.',
      'standards.create': 'Créer une norme',
      'standards.create_button': 'Créer une norme',
      'standards.table.standard': 'Norme',
      'standards.table.description': 'Description',
      'standards.table.controls': 'Contrôles',
      'standards.table.actions': 'Actions',
      'standards.controls.title': 'Contrôles',
      'standards.controls.add': 'Ajouter un contrôle',
      'standards.controls.none': 'Aucun contrôle défini.',
      
      // Analytics
      'analytics.title': 'Analytique',
      'analytics.subtitle': 'Métriques et tendances de conformité.',
      'analytics.compliance_rate': 'Taux de Conformité',
      'analytics.trend': 'Tendance',
      
      // Chat
      'chat.title': 'Chat de Conformité',
      'chat.subtitle': 'Posez des questions sur la conformité.',
      'chat.message_placeholder': 'Tapez votre question...',
      'chat.send': 'Envoyer',
      
      // Language
      'lang.title': 'Langue',
      'lang.english': 'English',
      'lang.french': 'Français',
    }
  },
  
  /**
   * Get translated string
   * @param {string} key - Translation key (e.g., 'documents.title')
   * @param {object} params - Optional parameters for string interpolation
   */
  t(key, params = {}) {
    let text = this.translations[this.currentLanguage]?.[key] || 
               this.translations['en'][key] || 
               key;
    
    // Simple string interpolation
    Object.keys(params).forEach(param => {
      text = text.replace(`{${param}}`, params[param]);
    });

    // Debug missing keys (helpful during development)
    if (text === key && key.includes('.')) {
      console.warn(`i18n: missing translation for key '${key}'`);
    }
    
    return text;
  },
  
  /**
   * Set language and persist
   */
  setLanguage(lang) {
    if (['en', 'fr'].includes(lang)) {
      this.currentLanguage = lang;
      localStorage.setItem('language', lang);
      this.updatePageText();
      console.log(`Language changed to: ${lang}`);
    }
  },
  
  /**
   * Get current language
   */
  getLanguage() {
    return this.currentLanguage;
  },
  
  /**
   * Update all page text with data-i18n attributes
   */
  updatePageText() {
    document.querySelectorAll('[data-i18n]').forEach(element => {
      const key = element.getAttribute('data-i18n');
      const text = this.t(key);
      
      if (element.tagName === 'INPUT' && element.type === 'placeholder') {
        element.placeholder = text;
      } else if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
        element.placeholder = text;
      } else if (element.tagName === 'TITLE') {
        document.title = text;
      } else {
        element.textContent = text;
      }
    });
  },
  
  /**
   * Initialize i18n
   */
  init() {
    this.updatePageText();
    console.log(`i18n initialized: ${this.currentLanguage}`);
    
    // Set placeholder for inputs
    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
      const key = element.getAttribute('data-i18n-placeholder');
      element.placeholder = this.t(key);
    });
  }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  i18n.init();
});

// Make i18n globally available
window.i18n = i18n;
