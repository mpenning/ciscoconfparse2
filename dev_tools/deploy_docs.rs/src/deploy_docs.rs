use log::info;
use rexpect::spawn;
use rexpect::error::*;

fn copy_and_extract_tarball() -> Result<(), Error> {
    // initialize colog for the logger...
    colog::init();

    ///////////////////////////////////////////////////////////////////////
    // scp the documentation file to remote webserver
    ///////////////////////////////////////////////////////////////////////
    info!("Starting file copy to chestnut");
    let mut sess = spawn("scp /home/mpenning/ccp2.tar.gz chestnut.he.net:", Some(45_000))?;
    sess.exp_eof()?;
    info!("  Finished file copy to chestnut");

    ///////////////////////////////////////////////////////////////////////
    // extract the tarball on the remote webserver with a 5-second timeout
    ///////////////////////////////////////////////////////////////////////
    info!("Starting tarball extraction");

    let mut sess = spawn("ssh chestnut.he.net", Some(5_000))?;
    let (_cmd_output, _matched_prompt) = sess.exp_regex("\\$")?;

    sess.send_line("cd public_html/py/ciscoconfparse2")?;
    let (_cmd_output, _matched_prompt) = sess.exp_regex("\\$")?;

    sess.send_line("rm -rf *")?;
    let (_cmd_output, _matched_prompt) = sess.exp_regex("\\$")?;

    sess.send_line("cp ~/ccp2.tar.gz .")?;
    let (_cmd_output, _matched_prompt) = sess.exp_regex("\\$")?;

    sess.send_line("tar xvfz ccp2.tar.gz")?;
    let (_cmd_output, _matched_prompt) = sess.exp_regex("\\$")?;

    sess.send_line("exit")?;
    sess.exp_eof()?;

    info!("  Finished tarball extraction");

    Ok(())

}

fn main() {
    copy_and_extract_tarball().unwrap_or_else(|e| panic!("doc deploy job failed with {}", e));
}
