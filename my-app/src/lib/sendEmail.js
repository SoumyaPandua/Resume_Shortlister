import nodemailer from 'nodemailer';

const host = process.env.SMTP_HOST;
const port = Number(process.env.SMTP_PORT || 587);
const user = process.env.SMTP_USER;
const pass = process.env.SMTP_PASS;

if (!host || !user || !pass) {
  console.error("[ERROR] Missing SMTP environment variables.");
}

// console.log("[DEBUG] SMTP Configuration:");
// console.log(`→ Host: ${host}`);
// console.log(`→ Port: ${port}`);
// console.log(`→ User: ${user}`);

let transporter;

function getTransporter() {
  if (!transporter) {
    transporter = nodemailer.createTransport({
      host,
      port,
      secure: port === 465, // true for 465, false for other ports
      auth: {
        user,
        pass,
      },
      logger: true,
    });

    transporter.verify((error, success) => {
      if (error) {
        console.error("[ERROR] SMTP verification failed:", error.message);
      } else {
        console.log("[DEBUG] SMTP server is ready.");
      }
    });
  }

  return transporter;
}

function generateResultsTable(results) {
  const rows = results.map(r => `
    <tr>
      <td>${r.resumeName}</td>
      <td>${r.jdName}</td>
      <td>${r.skillsMatch ?? '-'}%</td>
      <td>${r.jobRoleMatch ?? '-'}%</td>
      <td>${r.educationMatch ?? '-'}%</td>
      <td>${r.experienceMatch ?? '-'}%</td>
      <td>${r.overallScore ?? '-'}%</td>
      <td>${r.aiEstimate ?? '-'}%</td>
      <td>${r.shortlisted ? 'Yes' : 'No'}</td>
    </tr>
  `).join('');

  return `
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;font-size:13px;">
      <thead style="background-color:#f2f2f2;">
        <tr>
          <th>Resume Name</th>
          <th>JD Name</th>
          <th>Skill %</th>
          <th>Job Role %</th>
          <th>Education %</th>
          <th>Experience %</th>
          <th>Overall %</th>
          <th>AI Score %</th>
          <th>Shortlisted</th>
        </tr>
      </thead>
      <tbody>
        ${rows}
      </tbody>
    </table>
  `;
}

export default async function sendEmail(to, name, results) {
  console.log(`[DEBUG] Preparing to send email to: ${to}`);

  if (!Array.isArray(results) || results.length === 0) {
    console.warn("[WARN] No results to send.");
    return;
  }

  const shortlisted = results.filter(r => r.shortlisted).length;
  const total = results.length;
  const jdName = results[0]?.jdName || 'Unknown JD';

  const html = `
    <div style="font-family:Arial,sans-serif;padding:20px;">
      <h2>Hello ${name},</h2>
      <p>Your resume analysis has completed successfully.</p>
      <p><strong>${shortlisted} of ${total}</strong> resume(s) were shortlisted for the job description: <strong>${jdName}</strong>.</p>
      <br />
      ${generateResultsTable(results)}
      <br/>
      <p style="font-size: 0.9rem; color: #666;">This is an automated message from Resume Shortlister.</p>
    </div>
  `;

  const mailOptions = {
    from: `"Resume Shortlister" <${user}>`,
    to,
    subject: 'Your Resume Analysis Report',
    html,
  };

  try {
    const mailer = getTransporter();
    const info = await mailer.sendMail(mailOptions);
    console.log("[DEBUG] Email sent successfully:", info.messageId || info.response);
  } catch (err) {
    console.error("[ERROR] Failed to send email:", err.message);
    throw err;
  }
}